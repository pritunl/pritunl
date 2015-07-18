define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var KeyModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'key_url': null,
      'view_url': null,
      'uri_url': null
    },
    url: function() {
      return '/key/' + this.get('organization') + '/' + this.get('user');
    }
  });

  return KeyModel;
});
