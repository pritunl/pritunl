define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var OrgModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'name': null
    },
    url: function() {
      var url = '/organization';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return OrgModel;
});
