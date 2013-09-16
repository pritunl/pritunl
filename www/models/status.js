define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var StatusModel = Backbone.Model.extend({
    defaults: {
      'orgs_available': 2,
      'orgs_total': 2,
      'users_online': 18,
      'users_total': 64,
      'servers_online': 4,
      'servers_total': 4,
    },
    url: function() {
      return '/status';
    }
  });

  return StatusModel;
});
