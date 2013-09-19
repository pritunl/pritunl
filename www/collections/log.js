define([
  'jquery',
  'underscore',
  'backbone',
  'models/log'
], function($, _, Backbone, LogModel) {
  'use strict';
  var LogCollection = Backbone.Collection.extend({
    model: LogModel,
    url: function() {
      return '/log';
    }
  });

  return LogCollection;
});
