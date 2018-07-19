define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var LinkHostConfModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'name': null,
      'hostname': null,
      'conf': null,
      'ubnt_conf': null
    },
    url: function() {
      return '/link/' + this.get('link_id') + '/location/' +
        this.get('location_id') + '/host/' + this.get('id') + '/conf';
    }
  });

  return LinkHostConfModel;
});
