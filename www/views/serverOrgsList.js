define([
  'jquery',
  'underscore',
  'backbone',
  'collections/serverOrg',
  'views/list',
  'views/serverOrgsListItem',
  'text!templates/serverOrgsList.html'
], function($, _, Backbone, ServerOrgCollection, ListView,
    ServerOrgsListItemView, serverOrgsListTemplate) {
  'use strict';
  var ServerOrgsListView = ListView.extend({
    className: 'server-orgs-list',
    template: _.template(serverOrgsListTemplate),
    listErrorMsg: 'Failed to load server organizations, ' +
      'server error occurred.',
    initialize: function(options) {
      this.collection = new ServerOrgCollection({
        server: options.server
      });
      this.listenTo(window.events, 'servers_updated', this.update);
      ServerOrgsListView.__super__.initialize.call(this);
    },
    buildItem: function(model) {
      var modelView = new ServerOrgsListItemView({
        model: model
      });
      return modelView;
    },
    resetItems: function(views) {
      if (!views.length) {
        this.$('.no-orgs').slideDown(250);
      }
      else {
        this.$('.no-orgs').slideUp(250);
      }
    }
  });

  return ServerOrgsListView;
});
