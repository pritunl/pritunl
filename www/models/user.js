define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var UserModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'username': null,
      'expires': null
    },
    url: function() {
      var url = '/user';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return UserModel;
});
