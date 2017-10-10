define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var StateModel = Backbone.Model.extend({
    defaults: {
      'super_user': null,
      'csrf_token': null,
      'theme': null,
      'active': null,
      'plan': null,
      'version': null,
      'sso': null
    },
    url: function() {
      return '/state';
    }
  });

  return StateModel;
});
