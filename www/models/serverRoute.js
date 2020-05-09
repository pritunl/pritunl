define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var ServerRouteModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'server': null,
      'network': null,
      'comment': null,
      'metric': null,
      'virtual_network': null,
      'wg_network': null,
      'network_link': null,
      'server_link': null,
      'nat': null,
      'nat_interface': null,
      'nat_netmap': null,
      'net_gateway': null,
      'advertise': null,
      'vpc_region': null,
      'vpc_id': null
    },
    url: function() {
      var url = '/server/' + this.get('server') + '/route';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return ServerRouteModel;
});
