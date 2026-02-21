#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
from typing import List


def run(args: List[str]) -> None:
    result = subprocess.run(args)
    if result.returncode != 0:
        print(f"Error: '{' '.join(args)}' exited with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)


def is_net_cls_mounted() -> bool:
    with open('/proc/mounts', 'r') as f:
        for line in f:
            if line.startswith('net_cls /sys/fs/cgroup/net_cls cgroup '):
                return True
    return False


def write_file(path: str, value: str) -> None:
    with open(path, 'w') as f:
        f.write(value)


def get_default_dev() -> str:
    stdout = subprocess.check_output(
        ['ip', 'route', 'get', '8.8.8.8'],
        encoding='utf-8',
    )
    tokens = stdout.split()
    idx = tokens.index('dev')
    return tokens[idx + 1]


def cleanup(dev: str) -> None:
    subprocess.run(['tc', 'qdisc', 'del', 'dev', dev, 'root'])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run a command with netem network emulation applied.',
    )
    parser.add_argument(
        '--delay',
        nargs='+',
        metavar=('TIME', 'JITTER'),
        help='delay TIME [JITTER [CORRELATION]], e.g. --delay 100ms 10ms',
    )
    parser.add_argument(
        '--distribution',
        choices=['uniform', 'normal', 'pareto', 'paretonormal'],
        help='delay distribution (requires --delay)',
    )
    parser.add_argument(
        '--loss',
        nargs='+',
        metavar=('PERCENT', 'CORRELATION'),
        help='loss PERCENT [CORRELATION], e.g. --loss 1%%',
    )
    parser.add_argument(
        '--duplicate',
        nargs='+',
        metavar=('PERCENT', 'CORRELATION'),
        help='duplicate PERCENT [CORRELATION], e.g. --duplicate 0.1%%',
    )
    parser.add_argument(
        '--corrupt',
        nargs='+',
        metavar=('PERCENT', 'CORRELATION'),
        help='corrupt PERCENT [CORRELATION], e.g. --corrupt 0.1%%',
    )
    parser.add_argument(
        '--gap',
        metavar='DISTANCE',
        help='gap DISTANCE, e.g. --gap 5',
    )
    parser.add_argument(
        '--reorder',
        nargs='+',
        metavar=('PERCENT', 'CORRELATION'),
        help='reorder PERCENT [CORRELATION], e.g. --reorder 25%% (requires --delay)',
    )
    parser.add_argument(
        '-i',
        '--interface',
        metavar='DEVICE',
        help='network device to apply netem on (default: from `ip route get 8.8.8.8`)',
    )
    parser.add_argument(
        '-q',
        '--quiet',
        action='store_true',
        help='suppress informational output to stderr',
    )
    parser.add_argument(
        'command',
        nargs=argparse.REMAINDER,
        help='command to run (use -- to separate from netem options)',
    )
    args = parser.parse_args()
    if args.command and args.command[0] == '--':
        args.command = args.command[1:]
    if not args.command:
        parser.error('a command to run is required')
    if args.distribution and not args.delay:
        parser.error('--distribution requires --delay')
    if args.reorder and not args.delay:
        parser.error('--reorder requires --delay')
    return args


def build_netem_opts(args: argparse.Namespace) -> List[str]:
    opts: List[str] = []
    if args.delay:
        opts += ['delay'] + args.delay
    if args.distribution:
        opts += ['distribution', args.distribution]
    if args.loss:
        opts += ['loss'] + args.loss
    if args.duplicate:
        opts += ['duplicate'] + args.duplicate
    if args.corrupt:
        opts += ['corrupt'] + args.corrupt
    if args.gap:
        opts += ['gap', args.gap]
    if args.reorder:
        opts += ['reorder'] + args.reorder

    return opts


def main() -> None:
    args = parse_args()
    netem_opts = build_netem_opts(args)

    def log(msg: str):
        if not args.quiet:
            print(msg, file=sys.stderr)

    if args.interface:
        dev = args.interface
    else:
        dev = get_default_dev()
        log(f"Using network interface: {dev}")

    run(['modprobe', 'cls_cgroup'])
    run(['mkdir', '-p', '/sys/fs/cgroup/net_cls'])

    if not is_net_cls_mounted():
        run(['mount', '-t', 'cgroup', '-o', 'net_cls', 'net_cls', '/sys/fs/cgroup/net_cls'])

    run(['cgcreate', '-g', 'net_cls:test'])

    # Delete existing qdisc, ignore errors
    subprocess.run(
        ['tc', 'qdisc', 'del', 'dev', dev, 'root'],
        stderr=subprocess.DEVNULL,
    )

    run(['tc', 'qdisc', 'add', 'dev', dev, 'root', 'handle', '1:', 'prio'])
    run(['tc', 'filter', 'add', 'dev', dev, 'handle', '1:1', 'cgroup'])

    write_file('/sys/fs/cgroup/net_cls/net_cls.classid', '0x10002')
    write_file('/sys/fs/cgroup/net_cls/test/net_cls.classid', '0x10001')

    log(f"netem opts: {' '.join(netem_opts)}")
    run(['tc', 'qdisc', 'replace', 'dev', dev, 'parent', '1:1', 'netem'] + netem_opts)

    try:
        sys.exit(subprocess.run(['cgexec', '-g', 'net_cls:test'] + args.command).returncode)
    finally:
        cleanup(dev)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
