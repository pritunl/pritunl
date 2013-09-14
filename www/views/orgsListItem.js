define([
  'jquery',
  'underscore',
  'backbone',
  'views/usersList',
  'text!templates/orgsListItem.html'
], function($, _, Backbone, UsersListView, orgsListItemTemplate) {
  'use strict';
  var OrgsListItemView = Backbone.View.extend({
    template: _.template(orgsListItemTemplate),
    initialize: function() {
      this.usersListView = new UsersListView();
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      this.$('.users-list-container').append(this.usersListView.render().el);
      return this;
    }
  });

  return OrgsListItemView;
});
