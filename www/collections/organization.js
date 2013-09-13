define([
  'jquery',
  'underscore',
  'backbone',
  'models/organization'
], function($, _, Backbone, OrganizationModel) {
  'use strict';
  var OrganizationCollection = Backbone.Collection.extend({
    model: OrganizationModel,
    url: function() {
      return '/organization';
    }
  });

  return OrganizationCollection;
});
