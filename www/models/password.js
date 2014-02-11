define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var PasswordModel = Backbone.Model.extend({
    defaults: {
      'username': null,
      'password': null
    },
    url: function() {
      return '/auth';
    },
    isNew: function() {
      return false;
    }
  });

  return PasswordModel;
});
