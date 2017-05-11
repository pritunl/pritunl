define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var LinkLocationModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'link_id': null,
      'name': null,
      'status': null,
      'location': null,
      'quality': null,
      'hosts': null,
      'routes': null
    },
    initialize: function(attributes) {
      LinkLocationModel.__super__.initialize.call(this);
    },
    url: function() {
      var url = '/link/' + this.get('link_id') + '/location';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return LinkLocationModel;
});
