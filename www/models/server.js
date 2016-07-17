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
      'devices_online': null,
      'user_count': null,
      'network': null,
      'groups': null,
      'bind_address': null,
      'port': null,
      'protocol': null,
      'dh_param_bits': null,
      'ipv6': null,
      'ipv6_firewall': null,
      'network_mode': null,
      'network_start': null,
      'network_end': null,
      'restrict_routes': null,
      'multi_device': null,
      'dns_servers': null,
      'onc_hostname': null,
      'search_domain': null,
      'otp_auth': null,
      'cipher': null,
      'hash': null,
      'jumbo_frames': null,
      'lzo_compression': null,
      'inter_client': null,
      'ping_interval': null,
      'ping_timeout': null,
      'link_ping_interval': null,
      'link_ping_timeout': null,
      'max_clients': null,
      'replica_count': null,
      'vxlan': null,
      'dns_mapping': null,
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
