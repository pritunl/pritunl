define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var LogsModel = Backbone.Model.extend({
    defaults: {
      'output': null
    },
    url: function() {
      return '/logs';
    }
  });

  return LogsModel;
});
