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
      var location;
      var locations = response['locations'];

      if (locations) {
        for (var i = 0; i < locations.length; i++) {
          location = locations[i];

          if (location['hosts']) {
            location['hosts'] = new LinkHostCollection(location['hosts']);
          }

          if (location['routes']) {
            location['routes'] = new LinkRouteCollection(location['routes']);
          }
        }

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
