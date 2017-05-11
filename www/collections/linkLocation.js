define([
  'jquery',
  'underscore',
  'backbone',
  'models/linkLocation'
], function($, _, Backbone, LinkLocationModel) {
  'use strict';
  var LinkLocationCollection = Backbone.Collection.extend({
    model: LinkLocationModel,
    url: function() {
      return '/link/' + this.get('link_id') + '/location';
    }
  });

  return LinkLocationCollection;
});
