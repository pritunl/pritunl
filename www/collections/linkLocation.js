define([
  'jquery',
  'underscore',
  'backbone',
  'models/linkLocation'
], function($, _, Backbone, LinkLocationModel) {
  'use strict';
  var LinkLocationCollection = Backbone.Collection.extend({
    model: LinkLocationModel,
    initialize: function(options) {
      this.link = options.link;
    },
    url: function() {
      return '/link/' + this.link + '/location';
    }
  });

  return LinkLocationCollection;
});
