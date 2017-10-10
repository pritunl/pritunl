define([
  'jquery',
  'underscore',
  'backbone',
  'models/admin'
], function($, _, Backbone, AdminModel) {
  'use strict';
  var AdminCollection = Backbone.Collection.extend({
    model: AdminModel,
    url: function() {
      return '/admin';
    }
  });

  return AdminCollection;
});
