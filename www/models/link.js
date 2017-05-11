define([
  'jquery',
  'underscore',
  'backbone',
  'collections/linkLocation'
], function($, _, Backbone, LinkLocationCollection) {
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
      if (response['locations']) {
        response['locations'] = new LinkLocationCollection(
          response['locations']);
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
