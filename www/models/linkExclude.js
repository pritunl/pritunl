define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var LinkExcludeModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'link_id': null,
      'location_id': null,
      'network': null
    },
    url: function() {
      var url = '/link/' + this.get('link_id') + '/location/' +
        this.get('location_id') + '/exclude';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return LinkExcludeModel;
});
