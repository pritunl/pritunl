define([
  'jquery',
  'underscore',
  'backbone',
  'models/linkRoute'
], function($, _, Backbone, LinkRouteModel) {
  'use strict';
  var LinkRouteCollection = Backbone.Collection.extend({
    model: LinkRouteModel,
    url: function() {
      return '/link/' + this.get('link_id') + '/' +
        this.get('location_id') + '/route';
    }
  });

  return LinkRouteCollection;
});
