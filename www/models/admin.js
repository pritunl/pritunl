define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var AdminModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'username': null,
      'token': null,
      'secret': null,
      'otp_auth': null,
      'otp_secret': null,
      'audit': null
    },
    url: function() {
      var url = '/admin';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return AdminModel;
});
