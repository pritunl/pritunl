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
      'default_route': null,
      'network_link': null,
      'nat': null
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
