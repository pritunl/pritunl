define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var LinkTransitModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'link_id': null,
      'location_id': null,
      'transit_id': null,
      'name': null
    },
    url: function() {
      var url = '/link/' + this.get('link_id') + '/location/' +
        this.get('location_id') + '/transit';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return LinkTransitModel;
});
