define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var EventModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'time': null,
      'type': null
    }
  });

  return EventModel;
});
