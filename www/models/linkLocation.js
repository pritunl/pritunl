define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var LinkLocationModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'link_id': null,
      'link_type': null,
      'type': null,
      'ipv6': null,
      'name': null,
      'status': null,
      'location': null,
      'hosts': null,
      'routes': null,
      'peers': null
    },
    url: function() {
      var url = '/link/' + this.get('link_id') + '/location';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return LinkLocationModel;
});
