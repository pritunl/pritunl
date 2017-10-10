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
      'yubikey_id': null,
      'super_user': null,
      'auth_api': null,
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
    },
    destroyOtpSecret: function(options) {
      var otpSecret = this.get('otp_secret');
      this.save({
        otp_secret: true
      }, options);
      this.set({'otp_secret': otpSecret});
    }
  });

  return AdminModel;
});
