define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var ServerOutputModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'output': null
    },
    url: function() {
      return '/server/' + this.get('id') + '/output';
    }
  });

  return ServerOutputModel;
});
