define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var OrganizationModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'name': null,
      'expires': null
    },
    url: function() {
      var url = '/organization';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return OrganizationModel;
});
