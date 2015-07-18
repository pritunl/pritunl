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
        server: options.server.get('id')
      });
      this.listenTo(window.events, 'server_organizations_updated:' +
        options.server.get('id'), this.update);
      this.server = options.server;
      this.serverView = options.serverView;
      ServerOrgsListView.__super__.initialize.call(this);
    },
    buildItem: function(model) {
      var modelView = new ServerOrgsListItemView({
        model: model,
        server: this.server
      });
      return modelView;
    },
    resetItems: function(views) {
      if (!views.length) {
        this.$('.no-orgs').slideDown(window.slideTime);
      }
      else {
        this.$('.no-orgs').slideUp(window.slideTime);
      }
      this.serverView.updateOrgsCount();
      this.serverView.updateButtons();
    }
  });

  return ServerOrgsListView;
});
