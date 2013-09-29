define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var PasswordModel = Backbone.Model.extend({
    defaults: {
      'password': null
    },
    url: function() {
      return '/password';
    }
  });

  return PasswordModel;
});
