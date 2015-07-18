define([
  'jquery',
  'underscore',
  'backbone',
  'models/serverLink'
], function($, _, Backbone, ServerLinkModel) {
  'use strict';
  var ServerLinkCollection = Backbone.Collection.extend({
    model: ServerLinkModel,
    initialize: function(options) {
      this.server = options.server;
    },
    url: function() {
      return '/server/' + this.server + '/link';
    }
  });

  return ServerLinkCollection;
});
