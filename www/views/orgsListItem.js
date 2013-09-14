define([
  'jquery',
  'underscore',
  'backbone',
  'text!templates/orgsListItem.html'
], function($, _, Backbone, orgsListItemTemplate) {
  'use strict';
  var OrgsListItemView = Backbone.View.extend({
    template: _.template(orgsListItemTemplate),
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    }
  });

  return OrgsListItemView;
});
