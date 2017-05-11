define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var LinkRouteModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'network': null
    },
    url: function() {
      var url = '/link/' + this.get('link_id') + '/' +
        this.get('location_id') + '/route';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return LinkRouteModel;
});
