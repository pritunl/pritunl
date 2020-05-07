define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var HostModel = Backbone.Model.extend({
    defaults: {
      'name': null,
      'hostname': null,
      'instance_id': null,
      'status': null,
      'uptime': null,
      'version': null,
      'user_count': null,
      'users_online': null,
      'public_address': null,
      'public_addr': null,
      'public_address6': null,
      'public_addr6': null,
      'routed_subnet6': null,
      'routed_subnet6_wg': null,
      'proxy_ndp': null,
      'local_address': null,
      'local_addr': null,
      'local_address6': null,
      'local_addr6': null,
      'link_address': null,
      'availability_group': null
    },
    url: function() {
      var url = '/host';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return HostModel;
});
