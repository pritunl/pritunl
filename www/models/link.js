define([
  'jquery',
  'underscore',
  'backbone',
  'collections/linkLocation',
  'collections/linkHost',
  'collections/linkRoute'
], function($, _, Backbone, LinkLocationCollection, LinkHostCollection,
    LinkRouteCollection) {
  'use strict';
  var LinkModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'name': null,
      'status': null,
      'locations': null,
      'timeout': null
    },
    parse: function(response) {
      var locations = response['locations'];

      if (locations) {
        response['locations'] = new LinkLocationCollection(locations);
      }

      return response;
    },
    url: function() {
      var url = '/link';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return LinkModel;
});
