define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var LinkHostUriModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'name': null,
      'hostname': null,
      'uri': null
    },
    url: function() {
      return '/link/' + this.get('link_id') + '/location/' +
        this.get('location_id') + '/host/' + this.get('id') + '/uri';
    }
  });

  return LinkHostUriModel;
});
