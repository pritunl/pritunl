define([
  'jquery',
  'underscore',
  'backbone',
  'models/log'
], function($, _, Backbone, LogModel) {
  'use strict';
  var LogCollection = Backbone.Collection.extend({
    model: LogModel,
    initialize: function(options) {
      this.organization = options.organization;
    },
    url: function() {
      return '/logs';
    }
  });

  return LogCollection;
});
