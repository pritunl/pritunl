define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var AuthModel = Backbone.Model.extend({
    defaults: {
      'username': null,
      'password': null,
      'token': null,
      'secret': null,
      'default': null,
      'email_from': null,
      'email_api_key': null,
      'theme': null
    },
    url: function() {
      return '/auth';
    },
    isNew: function() {
      return false;
    }
  });

  return AuthModel;
});
