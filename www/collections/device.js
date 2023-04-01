define([
  'jquery',
  'underscore',
  'backbone',
  'models/device'
], function($, _, Backbone, DeviceModel) {
  'use strict';
  var DeviceCollection = Backbone.Collection.extend({
    model: DeviceModel,
    initialize: function() {
    },
    url: function() {
      return '/device/unregistered';
    },
    parse: function(response) {
      return response;
    }
  });

  return DeviceCollection;
});
