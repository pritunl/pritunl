define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var EventModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'type': null,
      'resource_id': null,
      'time': null
    }
  });

  return EventModel;
});
