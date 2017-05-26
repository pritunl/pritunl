define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var LinkHostModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'name': null,
      'timeout': null,
      'priority': null
    },
    url: function() {
      var url = '/link/' + this.get('link_id') + '/location/' +
        this.get('location_id') + '/host';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return LinkHostModel;
});
