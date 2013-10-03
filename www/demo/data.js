define([], function() {
  'use strict';
  /*jshint -W101:true, -W106:true, -W109:true */

  var auth = {
    'username': 'admin',
    'password': 'admin',
    'authenticated': false
  };

  var events = [];

  var logEntries = [];

  var orgs = {};

  var servers = {};

  return {
    auth: auth,
    events: events,
    logEntries: logEntries,
    orgs: orgs,
    servers: servers,
  };
});
