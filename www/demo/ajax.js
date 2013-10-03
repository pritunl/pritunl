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
      request.response({
        error: 'auth_not_valid',
        error_msg: 'Username or password is not valid.'
      }, 401);
      return;
    }
    request.response({});
  };
  routes['POST=/auth'] = authPost;

  var authGet = function(request) {
    request.response({
      authenticated: demoData.auth.authenticated
    });
  };
  routes['GET=/auth'] = authGet;

  var authDelete = function(request) {
    demoData.auth.authenticated = false;
    request.response({});
  };
  routes['DELETE=/auth'] = authDelete;

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
        request.response(events);
      }
      else {
        count += 1;
        if (count > (30 / 0.3)) {
          request.response([]);
        }
        else {
          checkEvents(request, lastEvent, count);
        }
      }
    }, 300);
  };

  var eventGet = function(request, lastEvent) {
    if (!lastEvent) {
      request.response([{
        id: uuid(),
        type: 'time',
        resource_id: null,
        time: Math.round(new Date().getTime() / 1000)
      }]);
      return;
    }

    checkEvents(request, lastEvent, 0);
  };
  routes['GET=/event'] = eventGet;
  routes['GET=/event/<int:lastEvent>'] = eventGet;

  var logGet = function(request) {
    request.response(demoData.logEntries);
  };
  routes['GET=/log'] = logGet;

  var organizationGet = function(request) {
    var id;
    var orgs = [];

    for (id in demoData.orgs) {
      orgs.push(demoData.orgs[id]);
    }

    request.response(orgs);
  };
  routes['GET=/organization'] = organizationGet;

  var organizationPostPut = function(request, orgId) {
    orgId = orgId || uuid();
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
    delete demoData.orgs[orgId];
    event('organizations_updated');
    request.response({});
  };
  routes['DELETE=/organization/<orgId>'] = organizationDelete;

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

    request.response(servers);
  };
  routes['GET=/server'] = serverGet;

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
    request.response({});
  };
  routes['POST=/server'] = serverPostPut;
  routes['PUT=/server/<serverId>'] = serverPostPut;

  var serverDelete = function(request, serverId) {
    delete demoData.servers[serverId];
    event('servers_updated');
    request.response({});
  };
  routes['DELETE=/server/<serverId>'] = serverDelete;

  var serverOrgGet = function(request, serverId) {
    var i;
    var orgId;
    var orgs = [];
    if (demoData.servers[serverId].orgs) {
      for (i = 0; i < demoData.servers[serverId].orgs.length; i++) {
        orgId = demoData.servers[serverId].orgs[i];
        orgs.push(_.extend({
          server: serverId
        }, demoData.orgs[orgId]));
      }
    }
    request.response(orgs);
  };
  routes['GET=/server/<serverId>/organization'] = serverOrgGet;

  var serverOrgPut = function(request, serverId, orgId) {
    if (!demoData.servers[serverId].orgs) {
      demoData.servers[serverId].orgs = [orgId];
    }
    else if (demoData.servers[serverId].orgs.indexOf(orgId) === -1) {
      demoData.servers[serverId].orgs.push(orgId);
    }
    event('server_organizations_updated', serverId);
    request.response({});
  };
  routes['PUT=/server/<serverId>/organization/<orgId>'] = serverOrgPut;

  var serverOrgDelete = function(request, serverId, orgId) {
    var index = demoData.servers[serverId].orgs.indexOf(orgId);
    if (index !== -1) {
      demoData.servers[serverId].orgs.splice(index, 1);
    }
    event('server_organizations_updated', serverId);
    request.response({});
  };
  routes['DELETE=/server/<serverId>/organization/<orgId>'] = serverOrgDelete;

  var serverOperationPut = function(request, serverId, operation) {
    if (operation === 'start') {
      demoData.servers[serverId].status = 'online';
      demoData.servers[serverId].output = demoData.serverOutput.online;
    }
    else if (operation === 'stop') {
      demoData.servers[serverId].status = 'offline';
      demoData.servers[serverId].output = demoData.serverOutput.offline;
    }
    else {
      demoData.servers[serverId].status = 'online';
      demoData.servers[serverId].output = demoData.serverOutput.online;
    }
    event('servers_updated');
    event('server_output_updated', serverId);
    request.response({});
  };
  routes['PUT=/server/<serverId>/<operation>'] = serverOperationPut;

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

    request.response({
      orgs_available: orgsCount,
      orgs_total: orgsCount,
      users_online: 8,
      users_total: 32,
      servers_online: serversOnlineCount,
      servers_total: serversCount,
      public_ip: '8.8.8.8',
    });
  };
  routes['GET=/status'] = statusGet;

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

    if (ajaxRequest.data && ajaxRequest.dataType === 'json') {
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
        setTimeout(function() {
          if (statusCode >= 200 && statusCode < 300) {
            status = 'success';
            ajaxRequest.success(data, jqXHR);
          }
          else {
            status = 'error';
            ajaxRequest.success(data, jqXHR);
          }
          ajaxRequest.complete(jqXHR, status);
        }, responseDelay);
      }
    };
    args.unshift(requestObj);

    if (!matched) {
      requestObj.response(null, 404);
      console.error(type, ajaxRequest.url, '404');
      return;
    }

    console.log(type, ajaxRequest.url);
    handler.apply(this, args);
  };

  return demoAjax;
});
