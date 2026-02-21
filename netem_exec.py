#!/usr/bin/env python3

import os
import subprocess
import sys


def run(*args):
    cmd = list(args)
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"Error: '{' '.join(cmd)}' exited with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)


def is_net_cls_mounted():
    with open('/proc/mounts', 'r') as f:
        for line in f:
            if line.startswith('net_cls /sys/fs/cgroup/net_cls cgroup '):
                return True
    return False


def write_file(path, value):
    with open(path, 'w') as f:
        f.write(value)


def get_default_dev():
    result = subprocess.run(
        ['ip', 'route', 'get', '8.8.8.8'],
        capture_output=True,
        text=True,
        check=True,
    )
    tokens = result.stdout.split()
    idx = tokens.index('dev')
    return tokens[idx + 1]


def cleanup(dev):
    subprocess.run(['tc', 'qdisc', 'del', 'dev', dev, 'root'])


def main():
    print("Init cgroup...", file=sys.stderr)

    dev = get_default_dev()
    print(f"Using network device: {dev}", file=sys.stderr)

    run('modprobe', 'cls_cgroup')
    run('mkdir', '-p', '/sys/fs/cgroup/net_cls')

    if not is_net_cls_mounted():
        run('mount', '-t', 'cgroup', '-o', 'net_cls', 'net_cls', '/sys/fs/cgroup/net_cls')

    run('cgcreate', '-g', 'net_cls:test')

    # Delete existing qdisc, ignore errors
    subprocess.run(
        ['tc', 'qdisc', 'del', 'dev', dev, 'root'],
        stderr=subprocess.DEVNULL,
    )

    run('tc', 'qdisc', 'add', 'dev', dev, 'root', 'handle', '1:', 'prio')
    run('tc', 'filter', 'add', 'dev', dev, 'handle', '1:1', 'cgroup')

    # TODO: status
    write_file('/sys/fs/cgroup/net_cls/net_cls.classid', '0x10002')
    write_file('/sys/fs/cgroup/net_cls/test/net_cls.classid', '0x10001')

    run('tc', 'qdisc', 'replace', 'dev', dev, 'parent', '1:1', 'netem', 'delay', '60ms')

    try:
        sys.exit(subprocess.run(['cgexec', '-g', 'net_cls:test', 'ping', 'ya.ru']).returncode)
    finally:
        cleanup(dev)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
