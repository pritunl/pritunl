define([
  'jquery',
  'underscore',
  'backbone',
  'models/serverRoute'
], function($, _, Backbone, ServerRouteModel) {
  'use strict';
  var ServerRouteCollection = Backbone.Collection.extend({
    model: ServerRouteModel,
    initialize: function(options) {
      this.server = options.server;
    },
    url: function() {
      return '/server/' + this.server + '/route';
    }
  });

  return ServerRouteCollection;
});
