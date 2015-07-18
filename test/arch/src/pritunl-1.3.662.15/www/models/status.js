define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var StatusModel = Backbone.Model.extend({
    defaults: {
      'org_count': null,
      'users_online': null,
      'user_count': null,
      'servers_online': null,
      'server_count': null,
      'server_version': null,
      'public_ip': null,
      'local_networks': null,
      'notification': null
    },
    url: function() {
      return '/status';
    }
  });

  return StatusModel;
});
