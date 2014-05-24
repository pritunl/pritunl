define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var UserModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'organization': null,
      'organization_name': null,
      'name': null,
      'email': null,
      'type': null,
      'status': null,
      'otp_auth': null,
      'otp_secret': null,
      'servers': null,
      'disabled': null
    },
    url: function() {
      var url = '/user/' + this.get('organization');

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    },
    destroyOtpSecret: function(options) {
      this.save(null, _.extend({
        url: this.url() + '/otp_secret'
      }, options));
    },
    parse: function(response) {
      this.set({'hidden': response.type !== 'client'});
      return response;
    }
  });

  return UserModel;
});
