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
      'type': null,
      'status': null,
      'uptime': null,
      'users_online': null,
      'user_count': null,
      'network': null,
      'interface': null,
      'port': null,
      'protocol': null,
      'dh_param_bits': null,
      'mode': null,
      'local_networks': null,
      'dns_servers': null,
      'search_domain': null,
      'public_address': null,
      'node_host': null,
      'node_port': null,
      'node_key': null,
      'otp_auth': null,
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
