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
      'users_total': null,
      'network': null,
      'interface': null,
      'port': null
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
