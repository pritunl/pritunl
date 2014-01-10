define([], function() {
  'use strict';
  /*jshint -W101:true, -W106:true, -W109:true */

  var auth = {
    username: 'demo',
    password: 'demo',
    authenticated: false
  };

  var events = [];

  var logs = [
    {
      id: '4eca4b80300347a2a237b1545bcfa728',
      message: 'Created new server "server2".',
      time: 1380863023
    },
    {
      id: '35e9b53b3e2c0d3bad674bcf4e7f2ba9',
      message: 'Created new server "server1".',
      time: 1380862905
    },
    {
      id: 'a66f7ec1117ac2708465adf3ab9cd6ec',
      message: 'Deleted user "user3".',
      time: 1380862844
    },
    {
      id: '126d5f9d78c7bd399484613f9aaf4383',
      message: 'Created new user "user3".',
      time: 1380862712
    },
    {
      id: 'ec21498ea20d9c9def138293a822a39c',
      message: 'Created new user "user2".',
      time: 1380862662
    },
    {
      id: '1e743b5234e32164837c89c2b706c1b7',
      message: 'Created new user "user1".',
      time: 1380862585
    },
    {
      id: '3dd359a679ec9772cc0c209d0d8c4cb4',
      message: 'Created new organization "org2".',
      time: 1380862472
    },
    {
      id: 'de50f62440b7bc39caaad622e5b3f402',
      message: 'Created new user "user4".',
      time: 1380862394
    },
    {
      id: '8e40c42302dbc14df2003febf611571c',
      message: 'Created new user "user3".',
      time: 1380862243
    },
    {
      id: '9fb1ece8c427767afe7adefa5fdb903f',
      message: 'Created new user "user2".',
      time: 1380862194
    },
    {
      id: '73cfe76951c4fe94df0d4cb12a6fbce7',
      message: 'Created new user "user1".',
      time: 1380862042
    },
    {
      id: 'c22c3996cbd8d44da469bae9e99ac57e',
      message: 'Created new organization "org1".',
      time: 1380861943
    },
    {
      id: '94bc0d3e2afa44ccb22c56843ac90c08',
      message: 'Web server started.',
      time: 1380861803
    }
  ];

  var orgs = {
    '55f5c6820e7a7de989916b4cdddf6070': {
      id: '55f5c6820e7a7de989916b4cdddf6070',
      name: 'org1'
    },
    'adb484e1f3c653dbc2aab10b14265dc6': {
      id: 'adb484e1f3c653dbc2aab10b14265dc6',
      name: 'org2'
    }
  };

  var servers = {
    '5310c28eacaeb3bd2a172c9db9ee1379': {
      id: '5310c28eacaeb3bd2a172c9db9ee1379',
      debug: false,
      otp_auth: true,
      lzo_compression: false,
      interface: 'tun0',
      local_network: null,
      name: 'server1',
      network: '10.139.17.0/24',
      orgs: [
        '55f5c6820e7a7de989916b4cdddf6070',
        'adb484e1f3c653dbc2aab10b14265dc6'
      ],
      output: 'Thu Oct  3 18:07:06 2013 OpenVPN 2.3.2 x86_64-unknown-linux-gnu [SSL (OpenSSL)] [LZO] [EPOLL] [eurephia] [MH] [IPv6] built on Jun  7 2013\nThu Oct  3 18:07:06 2013 NOTE: the current --script-security setting may allow this configuration to call user-defined scripts\nThu Oct  3 18:07:06 2013 TUN/TAP device tun0 opened\nThu Oct  3 18:07:06 2013 do_ifconfig, tt->ipv6=0, tt->did_ifconfig_ipv6_setup=0\nThu Oct  3 18:07:06 2013 /usr/bin/ip link set dev tun0 up mtu 1500\nThu Oct  3 18:07:06 2013 /usr/bin/ip addr add dev tun0 local 10.100.68.1 peer 10.100.68.2\nThu Oct  3 18:07:06 2013 UDPv4 link local (bound): [undef]\nThu Oct  3 18:07:06 2013 UDPv4 link remote: [undef]\nThu Oct  3 18:07:06 2013 Initialization Sequence Completed\n',
      port: '16070',
      protocol: 'udp',
      public_address: '8.8.8.8',
      status: true
    },
    '8159a073832f4bc481a1de9676326a9e': {
      id: '8159a073832f4bc481a1de9676326a9e',
      debug: false,
      otp_auth: true,
      lzo_compression: false,
      interface: 'tun1',
      local_network: null,
      name: 'server2',
      network: '10.113.56.0/24',
      orgs: [
        '55f5c6820e7a7de989916b4cdddf6070',
        'adb484e1f3c653dbc2aab10b14265dc6'
      ],
      output: 'Thu Oct  3 18:07:06 2013 OpenVPN 2.3.2 x86_64-unknown-linux-gnu [SSL (OpenSSL)] [LZO] [EPOLL] [eurephia] [MH] [IPv6] built on Jun  7 2013\nThu Oct  3 18:07:06 2013 NOTE: the current --script-security setting may allow this configuration to call user-defined scripts\nThu Oct  3 18:07:06 2013 TUN/TAP device tun0 opened\nThu Oct  3 18:07:06 2013 do_ifconfig, tt->ipv6=0, tt->did_ifconfig_ipv6_setup=0\nThu Oct  3 18:07:06 2013 /usr/bin/ip link set dev tun0 up mtu 1500\nThu Oct  3 18:07:06 2013 /usr/bin/ip addr add dev tun0 local 10.100.68.1 peer 10.100.68.2\nThu Oct  3 18:07:06 2013 UDPv4 link local (bound): [undef]\nThu Oct  3 18:07:06 2013 UDPv4 link remote: [undef]\nThu Oct  3 18:07:06 2013 Initialization Sequence Completed\n',
      port: '9430',
      protocol: 'udp',
      public_address: '8.8.8.8',
      status: true
    }
  };

  var serverOutput = {
    online: 'Thu Oct  3 18:07:06 2013 OpenVPN 2.3.2 x86_64-unknown-linux-gnu [SSL (OpenSSL)] [LZO] [EPOLL] [eurephia] [MH] [IPv6] built on Jun  7 2013\nThu Oct  3 18:07:06 2013 NOTE: the current --script-security setting may allow this configuration to call user-defined scripts\nThu Oct  3 18:07:06 2013 TUN/TAP device tun0 opened\nThu Oct  3 18:07:06 2013 do_ifconfig, tt->ipv6=0, tt->did_ifconfig_ipv6_setup=0\nThu Oct  3 18:07:06 2013 /usr/bin/ip link set dev tun0 up mtu 1500\nThu Oct  3 18:07:06 2013 /usr/bin/ip addr add dev tun0 local 10.100.68.1 peer 10.100.68.2\nThu Oct  3 18:07:06 2013 UDPv4 link local (bound): [undef]\nThu Oct  3 18:07:06 2013 UDPv4 link remote: [undef]\nThu Oct  3 18:07:06 2013 Initialization Sequence Completed\n',
    offline: 'Thu Oct  3 18:08:21 2013 event_wait : Interrupted system call (code=4)\nThu Oct  3 18:08:21 2013 /usr/bin/ip addr del dev tun0 local 10.100.68.1 peer 10.100.68.2\nThu Oct  3 18:08:21 2013 SIGINT[hard,] received, process exiting\n'
  };

  var users = {
    '55f5c6820e7a7de989916b4cdddf6070': {
      '47402514d02283610f92d681523863a7': {
        id: '47402514d02283610f92d681523863a7',
        name: 'user1',
        organization: '55f5c6820e7a7de989916b4cdddf6070',
        status: true,
        type: 'client',
        otp_auth: true,
        otp_secret: 'SF2GFRK5MQ7JB4TN',
        servers: [{
          real_address: '8.8.8.8',
          virt_address: '10.139.17.32',
          bytes_received: 55322869,
          bytes_sent: 24589107,
          connected_since: 1383170753
        }]
      },
      '9d33758bf6d559e2eb53e7e971248216': {
        id: '9d33758bf6d559e2eb53e7e971248216',
        name: 'user2',
        organization: '55f5c6820e7a7de989916b4cdddf6070',
        status: false,
        type: 'client',
        otp_auth: true,
        otp_secret: 'KBMSQM67TQR7CUYX',
        servers: []
      },
      'b5a694ee9411574964d05015add815cd': {
        id: 'b5a694ee9411574964d05015add815cd',
        name: 'user3',
        organization: '55f5c6820e7a7de989916b4cdddf6070',
        status: false,
        type: 'client',
        otp_auth: true,
        otp_secret: 'QF47Z3V2FWWLZRJZ',
        servers: []
      },
      '096b1604409d4fb791d2f11d2f0beddc': {
        id: '096b1604409d4fb791d2f11d2f0beddc',
        name: 'user4',
        organization: '55f5c6820e7a7de989916b4cdddf6070',
        status: false,
        type: 'client',
        otp_auth: true,
        otp_secret: 'YJGVC2JG2OZ7X45R',
        servers: []
      }
    },
    'adb484e1f3c653dbc2aab10b14265dc6': {
      '8834d44e44011e9aaede036e5ed6d483': {
        id: '8834d44e44011e9aaede036e5ed6d483',
        name: 'user1',
        organization: 'adb484e1f3c653dbc2aab10b14265dc6',
        status: false,
        type: 'client',
        otp_auth: true,
        otp_secret: 'QKKWOXSVCE6ODPFJ',
        servers: []
      },
      'f3b5ad1db481d07aed557d6d34b8cb78': {
        id: 'f3b5ad1db481d07aed557d6d34b8cb78',
        name: 'user2',
        organization: 'adb484e1f3c653dbc2aab10b14265dc6',
        status: false,
        type: 'client',
        otp_auth: true,
        otp_secret: 'DZVOQ6QW2R6OIMQA',
        servers: []
      }
    }
  };

  return {
    auth: auth,
    events: events,
    logs: logs,
    orgs: orgs,
    servers: servers,
    serverOutput: serverOutput,
    users: users
  };
});
