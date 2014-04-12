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
      'local_address': null,
      'remote_address': null,
      'connected_since': null,
      'virt_address': null,
      'real_address': null,
      'bytes_sent': null,
      'bytes_received': null
    }
  });

  return UserServerModel;
});
