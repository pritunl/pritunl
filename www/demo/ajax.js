define([
  'jquery',
  'underscore',
  'backbone',
  'demo/data'
], function($, _, Backbone, demoData) {
  'use strict';
  /* jshint -W106:true */
  var routes = {};
  var responseDelay = 75;

  var uuid = function() {
    var i;
    var id = '';
    for (i = 0; i < 8; i++) {
      id += Math.floor(
        (1 + Math.random()) * 0x10000).toString(16).substring(1);
    }
    return id;
  };

  var secretKey = function() {
    var i;
    var key = '';
    for (i = 0; i < 4; i++) {
      key += Math.random().toString(36).substr(2, 4).toUpperCase().replace(
        /0/g, '2').replace(/1/g, '3').replace(/8/g, '6').replace(/9/g, '7');
    }
    return key;
  }

  var authGet = function(request) {
    request.response({
      username: demoData.auth.username,
      token: demoData.auth.token,
      secret: demoData.auth.secret,
      email_from: demoData.auth.email_from,
      email_api_key: demoData.auth.email_api_key
    });
  };
  routes['GET=/auth'] = authGet;

  var authPut = function(request) {
    demoData.auth.username = request.data.username;
    demoData.auth.password = request.data.password;
    demoData.auth.email_from = request.data.email_from;
    demoData.auth.email_api_key = request.data.email_api_key;
    if (!request.data.token) {
      demoData.auth.token = uuid();
      demoData.auth.secret = uuid();
    }
    request.response({
      username: demoData.auth.username,
      token: demoData.auth.token,
      secret: demoData.auth.secret
    });
  };
  routes['PUT=/auth'] = authPut;

  var authSessionPost = function(request) {
    if (request.data.username !== demoData.auth.username ||
        request.data.password !== demoData.auth.password) {
      request.response({
        error: 'auth_invalid',
        error_msg: 'Username or password is not valid.'
      }, 401);
      return;
    }
    request.response({});
  };
  routes['POST=/auth/session'] = authSessionPost;

  var authSessionGet = function(request) {
    request.response({
      username: demoData.auth.username,
      authenticated: demoData.auth.authenticated
    });
  };
  routes['GET=/auth/session'] = authSessionGet;

  var authSessionDelete = function(request) {
    demoData.auth.authenticated = false;
    request.response({});
  };
  routes['DELETE=/auth/session'] = authSessionDelete;

  var subscriptionGet = function(request) {
    request.response(demoData.subscription);
  };
  routes['GET=/subscription'] = subscriptionGet;

  var subscriptionStateGet = function(request) {
    request.response({active: demoData.subscription.active});
  };
  routes['GET=/subscription/state'] = subscriptionStateGet;

  var subscriptionPost = function(request) {
    demoData.subscription.license = true;
    demoData.subscription.active = true;
    event('subscription_active');
    request.response(demoData.subscription);
  };
  routes['POST=/subscription'] = subscriptionPost;

  var subscriptionPut = function(request) {
    if (request.data.cancel) {
      demoData.subscription.cancel_at_period_end = true;
    }
    else {
      demoData.subscription.cancel_at_period_end = false;
    }
    request.response(demoData.subscription);
  };
  routes['PUT=/subscription'] = subscriptionPut;

  var subscriptionDelete = function(request) {
    demoData.subscription.license = false;
    demoData.subscription.active = false;
    event('subscription_inactive');
    request.response(demoData.subscription);
  };
  routes['DELETE=/subscription'] = subscriptionDelete;

  var event = function(type, resourceId) {
    demoData.events.push({
      id: uuid(),
      type: type,
      resource_id: resourceId || null,
      time: Math.round(new Date().getTime())
    });
  };

  var logEntry = function(message) {
    demoData.logs.unshift({
      id: uuid(),
      time: Math.round(new Date().getTime() / 1000),
      message: message
    });
    event('logs_updated');
  };

  var checkEvents = function(request, cursor, count) {
    setTimeout(function() {
      var i;
      var event;
      var events = [];
      if (cursor === undefined) {
        if (demoData.events.length) {
          cursor = demoData.events[demoData.events.length - 1].id;
        }
        else {
          cursor = null;
        }
      }
      if (count === undefined) {
        count = 0;
      }
      var cursorFound = cursor ? false : true;

      for (i = 0; i < demoData.events.length; i++) {
        event = demoData.events[i];
        if (cursorFound) {
          events.push(event);
        }
        else if (event.id === cursor) {
          cursorFound = true;
        }
      }

      if (events.length) {
        request.response(events);
      }
      else {
        count += 1;
        if (count > (30 / 0.1)) {
          request.response([]);
        }
        else {
          checkEvents(request, cursor, count);
        }
      }
    }, 100);
  };

  var eventGet = function(request, cursor) {
    checkEvents(request, cursor);
  };
  routes['GET=/event'] = eventGet;
  routes['GET=/event/<cursor>'] = eventGet;

  var logGet = function(request) {
    request.response(demoData.logs);
  };
  routes['GET=/log'] = logGet;

  var organizationGet = function(request) {
    var id;
    var userId;
    var orgs = [];
    var userCount;

    for (id in demoData.orgs) {
      userCount = 0;

      for (userId in demoData.users[id]) {
        if (demoData.users[id][userId].type === 'client') {
          userCount += 1;
        }
      }

      orgs.push(_.extend({
        user_count: userCount
      }, demoData.orgs[id]));
    }

    request.response(orgs);
  };
  routes['GET=/organization'] = organizationGet;

  var organizationPostPut = function(request, orgId) {
    if (!orgId) {
      orgId = uuid();
      demoData.users[orgId] = {};
      logEntry('Created new organization "' + request.data.name + '".');
    }
    demoData.orgs[orgId] = {
      id: orgId,
      name: request.data.name,
    };
    event('organizations_updated');
    request.response({});
  };
  routes['POST=/organization'] = organizationPostPut;
  routes['PUT=/organization/<orgId>'] = organizationPostPut;

  var organizationDelete = function(request, orgId) {
    var i;
    var serverId;

    for (serverId in demoData.servers) {
      for (i = 0; i < demoData.servers[serverId].orgs.length; i++) {
        if (demoData.servers[serverId].orgs[i] === orgId) {
          demoData.servers[serverId].orgs.splice(i, 1);
          event('server_organizations_updated', serverId);
          break;
        }
      }
    }

    var name = demoData.orgs[orgId].name;
    delete demoData.orgs[orgId];
    delete demoData.users[orgId];
    event('organizations_updated');
    logEntry('Deleted organization "' + name + '".');
    request.response({});
  };
  routes['DELETE=/organization/<orgId>'] = organizationDelete;

  var serverGet = function(request) {
    var i;
    var orgId;
    var userId;
    var serverId;
    var userCount;
    var servers = [];
    var serverStatus;

    for (serverId in demoData.servers) {
      userCount = 0;
      for (i = 0; i < demoData.servers[serverId].orgs.length; i++) {
        orgId = demoData.servers[serverId].orgs[i];
        for (userId in demoData.users[orgId]) {
          if (demoData.users[orgId][userId].type === 'client') {
            userCount += 1;
          }
        }
      }

      serverStatus = demoData.servers[serverId].status;
      servers.push(_.extend({
        users_online: serverStatus && userCount ? 1 : 0,
        user_count: userCount,
        org_count: demoData.servers[serverId].orgs.length
      }, demoData.servers[serverId]));
    }

    request.response(servers);
  };
  routes['GET=/server'] = serverGet;

  var serverPost = function(request) {
    var serverId = uuid();
    demoData.servers[serverId] = {
      id: serverId,
      name: request.data.name,
      type: request.data.type,
      network: request.data.network,
      interface: request.data.interface,
      port: request.data.port,
      protocol: request.data.protocol,
      dh_param_bits: request.data.dh_param_bits,
      mode: request.data.mode,
      local_networks: request.data.local_networks,
      dns_servers: request.data.dns_servers,
      search_domain: request.data.search_domain,
      public_address: request.data.public_address,
      otp_auth: request.data.otp_auth,
      lzo_compression: request.data.lzo_compression,
      debug: request.data.debug,
      node_host: request.data.node_host,
      node_port: request.data.node_port,
      node_key: request.data.node_key,
      status: false,
      orgs: [],
      output: ''
    };
    event('servers_updated');
    logEntry('Created new server "' + request.data.name + '".');
    request.response({});
  };
  routes['POST=/server'] = serverPost;

  var serverPut = function(request, serverId) {
    demoData.servers[serverId].name = request.data.name;
    demoData.servers[serverId].network = request.data.network;
    demoData.servers[serverId].interface = request.data.interface;
    demoData.servers[serverId].port = request.data.port;
    demoData.servers[serverId].protocol = request.data.protocol;
    demoData.servers[serverId].dh_param_bits = request.data.dh_param_bits;
    demoData.servers[serverId].mode = request.data.mode;
    demoData.servers[serverId].local_networks = request.data.local_networks;
    demoData.servers[serverId].dns_servers = request.data.dns_servers;
    demoData.servers[serverId].search_domain = request.data.search_domain;
    demoData.servers[serverId].public_address = request.data.public_address;
    demoData.servers[serverId].otp_auth = request.data.otp_auth;
    demoData.servers[serverId].lzo_compression = request.data.lzo_compression;
    demoData.servers[serverId].debug = request.data.debug;
    demoData.servers[serverId].node_host = request.data.node_host;
    demoData.servers[serverId].node_port = request.data.node_port;
    demoData.servers[serverId].node_key = request.data.node_key;
    event('servers_updated');
    request.response({});
  };
  routes['PUT=/server/<serverId>'] = serverPut;

  var serverDelete = function(request, serverId) {
    var name = demoData.servers[serverId].name;
    delete demoData.servers[serverId];
    event('servers_updated');
    logEntry('Deleted server "' + name + '".');
    request.response({});
  };
  routes['DELETE=/server/<serverId>'] = serverDelete;

  var serverOrgGet = function(request, serverId) {
    var i;
    var orgId;
    var orgs = [];
    for (i = 0; i < demoData.servers[serverId].orgs.length; i++) {
      orgId = demoData.servers[serverId].orgs[i];
      orgs.push(_.extend({
        server: serverId
      }, demoData.orgs[orgId]));
    }
    request.response(orgs);
  };
  routes['GET=/server/<serverId>/organization'] = serverOrgGet;

  var serverOrgPut = function(request, serverId, orgId) {
    if (demoData.servers[serverId].orgs.indexOf(orgId) === -1) {
      demoData.servers[serverId].orgs.push(orgId);
    }
    event('servers_updated');
    event('server_organizations_updated', serverId);
    request.response({});
  };
  routes['PUT=/server/<serverId>/organization/<orgId>'] = serverOrgPut;

  var serverOrgDelete = function(request, serverId, orgId) {
    var index = demoData.servers[serverId].orgs.indexOf(orgId);
    if (index !== -1) {
      demoData.servers[serverId].orgs.splice(index, 1);
    }
    event('servers_updated');
    event('server_organizations_updated', serverId);
    request.response({});
  };
  routes['DELETE=/server/<serverId>/organization/<orgId>'] = serverOrgDelete;

  var serverOperationPut = function(request, serverId, operation) {
    if (operation === 'start') {
      demoData.servers[serverId].status = true;
      demoData.servers[serverId].uptime = 1;
      demoData.servers[serverId].output = demoData.serverOutput.online;
      logEntry('Started server "' + demoData.servers[serverId].name + '".');
    }
    else if (operation === 'stop') {
      demoData.servers[serverId].status = false;
      demoData.servers[serverId].uptime = null;
      demoData.servers[serverId].output += demoData.serverOutput.offline;
      logEntry('Stopped server "' + demoData.servers[serverId].name + '".');
    }
    else {
      demoData.servers[serverId].status = true;
      demoData.servers[serverId].uptime = 1;
      demoData.servers[serverId].output += demoData.serverOutput.offline;
      demoData.servers[serverId].output += demoData.serverOutput.online;
      logEntry('Restarted server "' + demoData.servers[serverId].name + '".');
    }
    event('servers_updated');
    event('server_output_updated', serverId);
    request.response({});
  };
  routes['PUT=/server/<serverId>/<operation>'] = serverOperationPut;

  var serverOutputGet = function(request, serverId) {
    request.response({
      id: serverId,
      output: demoData.servers[serverId].output
    });
  };
  routes['GET=/server/<serverId>/output'] = serverOutputGet;

  var serverOutputDelete = function(request, serverId) {
    demoData.servers[serverId].output = '';
    event('server_output_updated', serverId);
    request.response({});
  };
  routes['DELETE=/server/<serverId>/output'] = serverOutputDelete;

  var serverBandwidthGet = function(request, serverId, period) {
    request.response(demoData.serverBandwidth[period]);
  };
  routes['GET=/server/<serverId>/bandwidth/<period>'] = serverBandwidthGet;

  var statusGet = function(request) {
    var orgId;
    var userId;
    var serverId;
    var orgsCount = 0;
    var usersCount = 0;
    var serversCount = 0;
    var serversOnlineCount = 0;

    for (orgId in demoData.orgs) {
      orgsCount += 1;
      for (userId in demoData.users[orgId]) {
        if (demoData.users[orgId][userId].type === 'client') {
          usersCount += 1;
        }
      }
    }

    for (serverId in demoData.servers) {
      serversCount += 1;
      if (demoData.servers[serverId].status) {
        serversOnlineCount += 1;
      }
    }

    request.response({
      org_count: orgsCount,
      users_online: usersCount ? 1 : 0,
      user_count: usersCount,
      servers_online: serversOnlineCount,
      server_count: serversCount,
      server_version: null,
      public_ip: '8.8.8.8',
      local_networks: [
        '10.10.0.0/24',
        '10.20.1.0/24',
        '10.30.2.0/24',
        '192.168.1.0/24'
      ],
      notification: ''
    });
  };
  routes['GET=/status'] = statusGet;

  var userGet = function(request, orgId) {
    var id;
    var users = [];
    var start = (new Date).getTime();
    var serverCount = 0;

    for (id in demoData.servers) {
      if (demoData.servers[id].orgs.indexOf(orgId) !== -1) {
        serverCount += 1;
      }
    }

    for (id in demoData.users[orgId]) {
      if (request.data.search &&
          demoData.users[orgId][id].name.toLowerCase().indexOf(
            request.data.search.toLowerCase()) !== 0) {
        continue;
      }
      users.push(_.extend({
        organization_name: demoData.orgs[orgId].name
      }, demoData.users[orgId][id]));
    }

    if (request.data.search) {
      request.response({
          search: request.data.search,
          search_more: false,
          search_limit: request.data.limit,
          search_count: users.length,
          search_time: ((new Date).getTime() - start + 10) / 1000,
          server_count: serverCount,
          users: users
      });
    }
    else {
      request.response({
          page: 0,
          page_total: 0,
          server_count: serverCount,
          users: users
      });
    }
  };
  routes['GET=/user/<orgId>'] = userGet;

  var userPost = function(request, orgId) {
    var userId = uuid();

    demoData.users[orgId][userId] = {
      id: userId,
      organization: orgId,
      name: request.data.name,
      email: request.data.email,
      type: 'client',
      status: false,
      otp_auth: true,
      otp_secret: secretKey(),
      servers: [{
        id: '5310c28eacaeb3bd2a172c9db9ee1379',
        name: 'server1',
        status: false,
        local_address: '10.54.0.12',
        remote_address: '10.54.0.13',
        real_address: null,
        virt_address: null,
        bytes_received: null,
        bytes_sent: null,
        connected_since: null
      }]
    };

    event('users_updated', orgId);
    logEntry('Created new user "' + request.data.name + '".');
    request.response({});
  };
  routes['POST=/user/<orgId>'] = userPost;

  var userPut = function(request, orgId, userId) {
    if (request.data.name) {
      demoData.users[orgId][userId].name = request.data.name;
    }
    if (request.data.email !== undefined) {
      demoData.users[orgId][userId].email = request.data.email;
    }
    if (request.data.disabled !== undefined) {
      demoData.users[orgId][userId].disabled = request.data.disabled;
    }
    event('users_updated', orgId);
    request.response({});
  };
  routes['PUT=/user/<orgId>/<userId>'] = userPut;

  var userDelete = function(request, orgId, userId) {
    var name = demoData.users[orgId][userId].name;
    delete demoData.users[orgId][userId];
    event('users_updated', orgId);
    logEntry('Deleted user "' + name + '".');
    request.response({});
  };
  routes['DELETE=/user/<orgId>/<userId>'] = userDelete;

  var userOtpSecretPut = function(request, orgId, userId) {
    demoData.users[orgId][userId].otp_secret = secretKey();
    event('users_updated', orgId);
    request.response({});
  };
  routes['PUT=/user/<orgId>/<userId>/otp_secret'] = userOtpSecretPut;

  var keyGet = function(request, orgId, userId) {
    request.response({
      id: uuid(),
      key_url: '/key/demo.tar',
      view_url: '/key/demo.html',
      uri_url: '/k/demo'
    });
  };
  routes['GET=/key/<org_id>/<user_id>'] = keyGet;

  var demoAjax = function(ajaxRequest) {
    var type = ajaxRequest.type;
    var url = ajaxRequest.url.split('/').splice(1);
    var i;
    var args;
    var route;
    var routeType;
    var typeIndex;
    var matched;
    var handler;
    var intChecked;

    for (intChecked = 0; intChecked < 2; intChecked++) {
      for (route in routes) {
        args = [];
        matched = true;
        handler = routes[route];
        typeIndex = route.indexOf('=');
        routeType = route.substr(0, typeIndex);
        route = route.substr(typeIndex + 1).split('/').splice(1);

        if (routeType !== type || url.length !== route.length) {
          matched = false;
          continue;
        }

        for (i = 0; i < url.length; i++) {
          if (route[i].substr(0, 1) === '<') {
            if (!intChecked && /^\d+$/.test(url[i])) {
              if (route[i].substr(0, 5) !== '<int:') {
                matched = false;
                break;
              }
              args.push(parseInt(url[i], 10));
            }
            else if (route[i].substr(0, 5) === '<int:') {
              matched = false;
              break;
            }
            else {
              args.push(url[i]);
            }
          }
          else if (url[i] !== route[i]) {
            matched = false;
            break;
          }
        }

        if (matched) {
          break;
        }
      }
      if (matched) {
        break;
      }
    }

    if (ajaxRequest.data && ajaxRequest.dataType === 'json' &&
        typeof ajaxRequest.data === 'string') {
      ajaxRequest.data = JSON.parse(ajaxRequest.data);
    }

    var requestObj = {
      dataType: ajaxRequest.dataType,
      contentType: ajaxRequest.contentType,
      data: ajaxRequest.data,
      response: function(data, statusCode) {
        statusCode = statusCode || 200;
        var status;
        var jqXHR = {
          status: statusCode,
          responseJSON: data
        };
        console.log(type, ajaxRequest.url, data);
        setTimeout(function() {
          if (statusCode >= 200 && statusCode < 300) {
            status = 'success';
            ajaxRequest.success(data, status, jqXHR);
          }
          else {
            status = 'error';
            ajaxRequest.error(jqXHR, status, null);
          }
          if (ajaxRequest.complete) {
            ajaxRequest.complete(jqXHR, status);
          }
        }, responseDelay);
      }
    };
    args.unshift(requestObj);

    if (!matched) {
      requestObj.response(null, 404);
      console.error(type, ajaxRequest.url, '404');
      return;
    }

    handler.apply(this, args);
  };

  return demoAjax;
});
