define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var KeyModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'organization': null,
      'user': null,
      'otp_auth': null,
      'url': null
    },
    url: function() {
      return '/key/' + this.get('organization') + '/' + this.get('user');
    }
  });

  return KeyModel;
});
