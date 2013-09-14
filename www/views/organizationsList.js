define([
  'jquery',
  'underscore',
  'backbone',
  'collections/organization',
  'text!templates/organizationsList.html'
], function($, _, Backbone, OrganizationCollection,
    organizationsListTemplate) {
  'use strict';
  var OrganizationsListView = Backbone.View.extend({
    template: _.template(organizationsListTemplate),
    render: function() {
      this.$el.html(this.template());
      return this;
    }
  });

  return OrganizationsListView;
});
