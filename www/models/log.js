define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var LogModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'date': null,
      'message': null
    },
    url: function() {
      var url = '/log';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return LogModel;
});
