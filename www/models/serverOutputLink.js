define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var ServerOutputLinkModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'output': null
    },
    url: function() {
      return '/server/' + this.get('id') + '/link_output';
    }
  });

  return ServerOutputLinkModel;
});
