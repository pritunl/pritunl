define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var ServerHostModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'server': null,
      'name': null,
      'address': null
    },
    url: function() {
      var url = '/server/' + this.get('server') + '/host';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return ServerHostModel;
});
