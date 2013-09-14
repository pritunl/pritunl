define([
  'jquery',
  'underscore',
  'backbone',
  'text!templates/organizationsListItem.html'
], function($, _, Backbone, organizationsListItemTemplate) {
  'use strict';
  var OrganizationsListItemView = Backbone.View.extend({
    template: _.template(organizationsListItemTemplate),
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    }
  });

  return OrganizationsListItemView;
});
