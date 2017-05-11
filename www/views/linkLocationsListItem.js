define([
  'jquery',
  'underscore',
  'backbone',
  'views/alert',
  'text!templates/linkLocationsListItem.html'
], function($, _, Backbone, AlertView, linkLocationsListItemTemplate) {
  'use strict';
  var LinkLocationsListItemView = Backbone.View.extend({
    className: 'link-location',
    template: _.template(linkLocationsListItemTemplate),
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    },
    update: function() {
      this.render();
    }
  });

  return LinkLocationsListItemView;
});
