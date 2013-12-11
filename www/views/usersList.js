define([
  'jquery',
  'underscore',
  'backbone',
  'collections/user',
  'views/list',
  'views/usersListItem',
  'text!templates/usersList.html'
], function($, _, Backbone, UserCollection, ListView, UsersListItemView,
    usersListTemplate) {
  'use strict';
  var UsersListView = ListView.extend({
    className: 'users-list-container',
    template: _.template(usersListTemplate),
    listErrorMsg: 'Failed to load users, server error occurred.',
    initialize: function(options) {
      this.collection = new UserCollection({
        org: options.org
      });
      this.listenTo(window.events, 'users_updated', this.update);
      this.listenTo(window.events, 'organizations_updated', this.update);
      UsersListView.__super__.initialize.call(this);
    },
    removeItem: function(view) {
      if (view.getSelect()) {
        view.setSelect(false);
      }
      view.destroy();
    },
    onSelect: function(view) {
      this.trigger('select', view);
    },
    buildItem: function(model) {
      var modelView = new UsersListItemView({
        model: model
      });
      this.listenTo(modelView, 'select', this.onSelect);
      return modelView;
    },
    resetItems: function(views) {
      if (!views.length) {
        this.$('.no-users').slideDown(250);
      }
      else {
        this.$('.no-users').slideUp(250);
      }
    }
  });

  return UsersListView;
});
