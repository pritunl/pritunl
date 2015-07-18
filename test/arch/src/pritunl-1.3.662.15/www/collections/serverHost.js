define([
  'jquery',
  'underscore',
  'backbone',
  'models/serverHost'
], function($, _, Backbone, ServerHostModel) {
  'use strict';
  var ServerHostCollection = Backbone.Collection.extend({
    model: ServerHostModel,
    initialize: function(options) {
      this.server = options.server;
    },
    url: function() {
      return '/server/' + this.server + '/host';
    }
  });

  return ServerHostCollection;
});
