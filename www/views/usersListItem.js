define([
  'jquery',
  'underscore',
  'backbone',
  'text!templates/usersListItem.html'
], function($, _, Backbone, usersListItemTemplate) {
  'use strict';
  var UsersListItemView = Backbone.View.extend({
    template: _.template(usersListItemTemplate),
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    }
  });

  return UsersListItemView;
});
