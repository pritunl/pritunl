define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var HostModel = Backbone.Model.extend({
    defaults: {
      'name': null,
      'status': null,
      'uptime': null,
      'user_count': null,
      'users_online': null,
      'public_address': null
    },
    url: function() {
      var url = '/host';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return HostModel;
});
