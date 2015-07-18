define([
  'jquery',
  'underscore',
  'backbone',
  'models/serverOrg'
], function($, _, Backbone, ServerOrgModel) {
  'use strict';
  var ServerOrgCollection = Backbone.Collection.extend({
    model: ServerOrgModel,
    initialize: function(options) {
      this.server = options.server;
    },
    url: function() {
      return '/server/' + this.server + '/organization';
    }
  });

  return ServerOrgCollection;
});
