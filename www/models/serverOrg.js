define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var ServerOrgModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'server': null,
      'name': null
    },
    url: function() {
      var url = '/server/' + this.get('server') + '/organization';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return ServerOrgModel;
});
