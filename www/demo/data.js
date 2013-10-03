define([], function() {
  'use strict';
  /*jshint -W101:true, -W106:true, -W109:true */

  var auth = {
    username: 'admin',
    password: 'admin',
    authenticated: false
  };

  var events = [];

  var logEntries = [];

  var orgs = {};

  var servers = {};

  var serverOutput = {
    online: 'Thu Oct  3 18:07:06 2013 OpenVPN 2.3.2 x86_64-unknown-linux-gnu [SSL (OpenSSL)] [LZO] [EPOLL] [eurephia] [MH] [IPv6] built on Jun  7 2013\nThu Oct  3 18:07:06 2013 NOTE: the current --script-security setting may allow this configuration to call user-defined scripts\nThu Oct  3 18:07:06 2013 TUN/TAP device tun0 opened\nThu Oct  3 18:07:06 2013 do_ifconfig, tt->ipv6=0, tt->did_ifconfig_ipv6_setup=0\nThu Oct  3 18:07:06 2013 /usr/bin/ip link set dev tun0 up mtu 1500\nThu Oct  3 18:07:06 2013 /usr/bin/ip addr add dev tun0 local 10.100.68.1 peer 10.100.68.2\nThu Oct  3 18:07:06 2013 UDPv4 link local (bound): [undef]\nThu Oct  3 18:07:06 2013 UDPv4 link remote: [undef]\nThu Oct  3 18:07:06 2013 Initialization Sequence Completed',
    offline: 'Thu Oct  3 18:07:06 2013 OpenVPN 2.3.2 x86_64-unknown-linux-gnu [SSL (OpenSSL)] [LZO] [EPOLL] [eurephia] [MH] [IPv6] built on Jun  7 2013\nThu Oct  3 18:07:06 2013 NOTE: the current --script-security setting may allow this configuration to call user-defined scripts\nThu Oct  3 18:07:06 2013 TUN/TAP device tun0 opened\nThu Oct  3 18:07:06 2013 do_ifconfig, tt->ipv6=0, tt->did_ifconfig_ipv6_setup=0\nThu Oct  3 18:07:06 2013 /usr/bin/ip link set dev tun0 up mtu 1500\nThu Oct  3 18:07:06 2013 /usr/bin/ip addr add dev tun0 local 10.100.68.1 peer 10.100.68.2\nThu Oct  3 18:07:06 2013 UDPv4 link local (bound): [undef]\nThu Oct  3 18:07:06 2013 UDPv4 link remote: [undef]\nThu Oct  3 18:07:06 2013 Initialization Sequence Completed\nThu Oct  3 18:08:21 2013 event_wait : Interrupted system call (code=4)\nThu Oct  3 18:08:21 2013 /usr/bin/ip addr del dev tun0 local 10.100.68.1 peer 10.100.68.2\nThu Oct  3 18:08:21 2013 SIGINT[hard,] received, process exiting'
  };

  return {
    auth: auth,
    events: events,
    logEntries: logEntries,
    orgs: orgs,
    servers: servers,
    serverOutput: serverOutput
  };
});
