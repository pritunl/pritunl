define([
  'jquery',
  'underscore',
  'backbone',
  'models/host'
], function($, _, Backbone, HostModel) {
  'use strict';
  var HostCollection = Backbone.Collection.extend({
    model: HostModel,
    url: function() {
      return '/host';
    }
  });

  return HostCollection;
});
