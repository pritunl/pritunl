define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var ServerModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'name': null,
      'status': null,
      'uptime': null,
      'users_online': null,
      'user_count': null,
      'network': null,
      'port': null,
      'protocol': null,
      'dh_param_bits': null,
      'mode': null,
      'local_networks': null,
      'dns_servers': null,
      'search_domain': null,
      'otp_auth': null,
      'cipher': null,
      'jumbo_frames': null,
      'lzo_compression': null,
      'debug': null
    },
    url: function() {
      var url = '/server';

      if (this.get('id')) {
        url += '/' + this.get('id');

        if (this.get('operation')) {
          url += '/' + this.get('operation');
        }
      }

      return url;
    }
  });

  return ServerModel;
});
