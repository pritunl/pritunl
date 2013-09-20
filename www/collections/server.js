define([
  'jquery',
  'underscore',
  'backbone',
  'models/server'
], function($, _, Backbone, ServerModel) {
  'use strict';
  var ServerCollection = Backbone.Collection.extend({
    model: ServerModel,
    url: function() {
      return '/server';
    }
  });

  return ServerCollection;
});
