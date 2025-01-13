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
      'network_wg': null,
      'groups': null,
      'bind_address': null,
      'dynamic_firewall': null,
      'geo_sort': null,
      'route_dns': null,
      'device_auth': null,
      'port': null,
      'port_wg': null,
      'protocol': null,
      'dh_param_bits': null,
      'ipv6': null,
      'ipv6_firewall': null,
      'network_mode': null,
      'network_start': null,
      'network_end': null,
      'restrict_routes': null,
      'wg': null,
      'multi_device': null,
      'dns_servers': null,
      'search_domain': null,
      'otp_auth': null,
      'sso_auth': null,
      'cipher': null,
      'hash': null,
      'block_outside_dns': null,
      'jumbo_frames': null,
      'lzo_compression': null,
      'inter_client': null,
      'ping_interval': null,
      'ping_timeout': null,
      'ping_interval_wg': null,
      'ping_timeout_wg': null,
      'link_ping_interval': null,
      'link_ping_timeout': null,
      'inactive_timeout': null,
      'session_timeout': null,
      'allowed_devices': null,
      'max_clients': null,
      'max_devices': null,
      'replica_count': null,
      'vxlan': null,
      'dns_mapping': null,
      'debug': null,
      'pre_connect_msg': null,
      'mss_fix': null,
      'multihome': null
    },
    url: function() {
      var url = '/server';

      if (this.get('id')) {
        url += '/' + this.get('id');

        if (this.get('operation')) {
          url += '/operation/' + this.get('operation');
        }
      }

      return url;
    }
  });

  return ServerModel;
});
