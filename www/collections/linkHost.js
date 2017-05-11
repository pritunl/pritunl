define([
  'jquery',
  'underscore',
  'backbone',
  'models/linkHost'
], function($, _, Backbone, LinkHostModel) {
  'use strict';
  var LinkHostCollection = Backbone.Collection.extend({
    model: LinkHostModel,
    url: function() {
      return '/link/' + this.get('link_id') + '/' +
        this.get('location_id') + '/host';
    }
  });

  return LinkHostCollection;
});
