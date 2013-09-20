define([
  'jquery',
  'underscore',
  'backbone',
  'text!templates/serverOrgsListItem.html'
], function($, _, Backbone, serverOrgsListItemTemplate) {
  'use strict';
  var ServerOrgsListItemView = Backbone.View.extend({
    className: 'org',
    template: _.template(serverOrgsListItemTemplate),
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    },
    update: function() {
    }
  });

  return ServerOrgsListItemView;
});
