define([
  'jquery',
  'underscore',
  'backbone',
  'collections/userServer',
  'views/list',
  'views/userServersListItem',
  'text!templates/userServersList.html'
], function($, _, Backbone, UserServerCollection, ListView,
    UserServersListItemView, userServersListTemplate) {
  'use strict';
  var ServerOrgsListView = ListView.extend({
    className: 'user-servers',
    template: _.template(userServersListTemplate),
    listErrorMsg: 'Failed to load user information, ' +
      'server error occurred.',
    initialize: function(options) {
      this.models = options.models;
      this.collection = new UserServerCollection();
      ServerOrgsListView.__super__.initialize.call(this);
    },
    buildItem: function(model) {
      return new UserServersListItemView({
        model: model
      });
    },
    update: function(models) {
      if (models === undefined) {
        models = this.models;
      }
      this.collection.reset(models);
    },
    resetItems: function(views) {
      if (!views.length) {
        this.$('.no-servers').slideDown(250);
      }
      else {
        this.$('.no-servers').slideUp(250);
      }
    }
  });

  return ServerOrgsListView;
});
