# netem-exec

`netem-exec` is a simple command runner under [tc-netem(8)](https://manpages.debian.org/testing/iproute2/tc-netem.8.en.html).
It can emulate network delays, jitter, packet loss, etc.

# Examples

Ping with no delay:
```sh
$ ping -c 4 8.8.8.8
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=105 time=22.2 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=105 time=20.7 ms
64 bytes from 8.8.8.8: icmp_seq=3 ttl=105 time=22.1 ms
64 bytes from 8.8.8.8: icmp_seq=4 ttl=105 time=22.4 ms

--- 8.8.8.8 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3004ms
rtt min/avg/max/mdev = 20.654/21.849/22.401/0.698 ms
```

Ping with 200ms delay:
```sh
$ netem-exec --sudo --delay 200ms -- ping -c 4 8.8.8.8
Using network interface: tun0
netem opts: delay 200ms
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=105 time=221 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=105 time=222 ms
64 bytes from 8.8.8.8: icmp_seq=3 ttl=105 time=220 ms
64 bytes from 8.8.8.8: icmp_seq=4 ttl=105 time=222 ms

--- 8.8.8.8 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3000ms
rtt min/avg/max/mdev = 220.076/221.360/222.304/0.922 ms
```

Help:
```
$ ./netem-exec -h
usage: netem-exec [-h] [--delay TIME [JITTER ...]] [--distribution {uniform,normal,pareto,paretonormal}] [--loss PERCENT [CORRELATION ...]]
                  [--duplicate PERCENT [CORRELATION ...]] [--corrupt PERCENT [CORRELATION ...]] [--gap DISTANCE] [--rate RATE] [--reorder PERCENT [CORRELATION ...]]
                  [-s] [-i DEVICE] [-q]
                  ...

Run a command with netem network emulation applied.

positional arguments:
  command               command to run (use -- to separate from netem options)

options:
  -h, --help            show this help message and exit
  --delay TIME [JITTER ...]
                        delay TIME [JITTER [CORRELATION]], e.g. --delay 100ms 10ms
  --distribution {uniform,normal,pareto,paretonormal}
                        delay distribution (requires --delay)
  --loss PERCENT [CORRELATION ...]
                        loss PERCENT [CORRELATION], e.g. --loss 1%
  --duplicate PERCENT [CORRELATION ...]
                        duplicate PERCENT [CORRELATION], e.g. --duplicate 0.1%
  --corrupt PERCENT [CORRELATION ...]
                        corrupt PERCENT [CORRELATION], e.g. --corrupt 0.1%
  --gap DISTANCE        gap DISTANCE, e.g. --gap 5
  --rate RATE           rate limit, e.g. --rate 1mbit
  --reorder PERCENT [CORRELATION ...]
                        reorder PERCENT [CORRELATION], e.g. --reorder 25% (requires --delay)
  -s, --sudo            run privileged commands with sudo
  -i DEVICE, --interface DEVICE
                        network device to apply netem on (default: from `ip route get 8.8.8.8`)
  -q, --quiet           suppress informational output to stderr
```
