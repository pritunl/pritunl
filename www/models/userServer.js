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
      'type': null,
      'client_id': null,
      'device_id': null,
      'device_name': null,
      'real_address': null,
      'virt_address': null,
      'connected_since': null
    }
  });

  return UserServerModel;
});
