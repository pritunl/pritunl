define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var AuthModel = Backbone.Model.extend({
    defaults: {
      'authenticated': null,
      'username': null,
      'password': null
    },
    url: function() {
      return '/auth/session';
    }
  });

  return AuthModel;
});
