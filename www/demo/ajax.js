define([
  'jquery',
  'underscore',
  'backbone',
  'demo/data'
], function($, _, Backbone, demoData) {
  'use strict';
  /*jshint -W106:true */
  var routes = {};
  var responseDelay = 150;

  var uuid = function() {
    var id = '';
    id += Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
    id += Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
    id += Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
    id += Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
    id += Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
    id += Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
    id += Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
    id += Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
    return id;
  };

  var authPost = function(request) {
    if (request.data.username !== demoData.auth.username ||
        request.data.password !== demoData.auth.password) {
      setTimeout(function() {
        request.error({
          responseJSON: {
            error: 'auth_not_valid',
            error_msg: 'Username or password is not valid.'
          },
          status: 401
        });
      }, responseDelay);
      return;
    }

    setTimeout(function() {
      request.success({});
    }, responseDelay);
  };
  routes['POST+auth'] = authPost;

  var authGet = function(request) {
    setTimeout(function() {
      request.success({
        authenticated: demoData.auth.authenticated
      });
    }, responseDelay);
  };
  routes['GET+auth'] = authGet;

  var authDelete = function(request) {
    demoData.auth.authenticated = false;
    setTimeout(function() {
      request.success({});
    }, responseDelay);
  };
  routes['DELETE+auth'] = authDelete;

  var event = function(type, resourceId) {
    demoData.events.push({
      id: uuid(),
      type: type,
      resource_id: resourceId || null,
      time: Math.round(new Date().getTime() / 1000)
    });
  }

  var checkEvents = function(request, lastEvent, count) {
    setTimeout(function() {
      var i;
      var event;
      var events = [];

      for (i = 0; i < demoData.events.length; i++) {
        event = demoData.events[i];
        if (event.time <= lastEvent) {
          continue;
        }
        events.push(event);
      }

      if (events.length) {
        request.success(events);
      }
      else {
        count += 1;
        if (count > (30 / 0.3)) {
          request.success([]);
        }
        else {
          checkEvents(request, lastEvent, count);
        }
      }
    }, 300);
  };

  var eventGet = function(request, lastEvent) {
    lastEvent = parseInt(lastEvent, 10);
    if (!lastEvent) {
      request.success([{
        id: uuid(),
        type: 'time',
        resource_id: null,
        time: Math.round(new Date().getTime() / 1000)
      }]);
      return;
    }

    checkEvents(request, lastEvent, 0);
  };
  routes['GET+event'] = eventGet;

  var logGet = function(request) {
    setTimeout(function() {
      request.success(demoData.logEntries);
    }, responseDelay);
  };
  routes['GET+log'] = logGet;

  var organizationGet = function(request) {
    var id;
    var orgs = [];

    for (id in demoData.orgs) {
      orgs.push(demoData.orgs[id]);
    }

    setTimeout(function() {
      request.success(orgs);
    }, responseDelay);
  };
  routes['GET+organization'] = organizationGet;

  var organizationPostPut = function(request, orgId) {
    orgId = orgId || uuid();
    demoData.orgs[orgId] = {
      id: orgId,
      name: request.data.name,
    };
    event('organizations_updated');
    setTimeout(function() {
      request.success({});
    }, responseDelay);
  };
  routes['POST+organization'] = organizationPostPut;
  routes['PUT+organization'] = organizationPostPut;

  var organizationDelete = function(request, orgId) {
    delete demoData.orgs[orgId];
    event('organizations_updated');
    setTimeout(function() {
      request.success({});
    }, responseDelay);
  };
  routes['DELETE+organization'] = organizationDelete;

  var serverGet = function(request) {
    var id;
    var servers = [];
    var serverStatus;

    for (id in demoData.servers) {
      serverStatus = demoData.servers[id].status || 'offline';
      servers.push(_.extend({
        status: serverStatus,
        uptime: serverStatus === 'online' ? 109800 : null,
        users_online: serverStatus === 'online' ? 8 : 0,
        users_total: '32',
        org_count: 4,
      }, demoData.servers[id]));
    }

    setTimeout(function() {
      request.success(servers);
    }, responseDelay);
  };
  routes['GET+server'] = serverGet;

  var serverPostPut = function(request, serverId) {
    serverId = serverId || uuid();
    demoData.servers[serverId] = _.extend({
      id: serverId,
      name: request.data.name,
      network: request.data.network,
      interface: request.data.interface,
      port: request.data.port,
      protocol: request.data.protocol,
      local_network: request.data.local_network,
      public_address: request.data.public_address,
      debug: request.data.debug
    }, demoData.servers[serverId]);
    event('servers_updated');
    setTimeout(function() {
      request.success({});
    }, responseDelay);
  };
  routes['POST+server'] = serverPostPut;
  routes['PUT+server'] = serverPostPut;

  var serverDelete = function(request, serverId) {
    delete demoData.servers[serverId];
    event('servers_updated');
    setTimeout(function() {
      request.success({});
    }, responseDelay);
  };
  routes['DELETE+server'] = serverDelete;

  var serverDelete = function(request, serverId) {
    delete demoData.servers[serverId];
    event('servers_updated');
    setTimeout(function() {
      request.success({});
    }, responseDelay);
  };
  routes['DELETE+server'] = serverDelete;

  var statusGet = function(request) {
    var id;
    var orgsCount = 0;
    var serversCount = 0;
    var serversOnlineCount = 0;

    for (id in demoData.orgs) {
      orgsCount += 1;
    }

    for (id in demoData.servers) {
      serversCount += 1;
      if (demoData.servers[id].status === 'online') {
        serversOnlineCount += 1;
      }
    }

    setTimeout(function() {
      request.success({
        orgs_available: orgsCount,
        orgs_total: orgsCount,
        users_online: 8,
        users_total: 32,
        servers_online: serversOnlineCount,
        servers_total: serversCount,
        public_ip: '8.8.8.8',
      });
    }, responseDelay);
  };
  routes['GET+status'] = statusGet;

  var demoAjax = function(request) {
    var url = request.url.split('/');
    var method = url.splice(1, 1)[0];
    var vars = url.splice(1);
    var type = request.type;
    vars.unshift(request);

    if (request.data && request.dataType === 'json') {
      request.data = JSON.parse(request.data);
    }

    window.console.log(type, method, vars);

    if (routes[type + '+' + method]) {
      routes[type + '+' + method].apply(this, vars);
    }
  };

  return demoAjax;
});
