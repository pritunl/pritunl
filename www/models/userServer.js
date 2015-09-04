define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var UserServerModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'name': null,
      'status': null,
      'server_id': null,
      'device_id': null,
      'device_name': null,
      'platform': null,
      'real_address': null,
      'virt_address': null,
      'connected_since': null
    }
  });

  return UserServerModel;
});
