define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var ServerModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'uptime': '128 days 12 hrs 34 mins',
      'users_online': 12,
      'users_total': 32,
      'network': '10.232.128.0/24',
      'interface': 'tun0',
      'port': '12345/udp'
    },
    url: function() {
      var url = '/server';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return ServerModel;
});
