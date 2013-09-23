define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var StatusModel = Backbone.Model.extend({
    defaults: {
      'orgs_available': null,
      'orgs_total': null,
      'users_online': null,
      'users_total': null,
      'servers_online': null,
      'servers_total': null
    },
    url: function() {
      return '/status';
    }
  });

  return StatusModel;
});
