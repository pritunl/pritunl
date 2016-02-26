define([
  'jquery',
  'underscore',
  'backbone',
  'collections/serverHost',
  'views/list',
  'views/serverHostsListItem',
  'text!templates/serverHostsList.html'
], function($, _, Backbone, ServerHostCollection, ListView,
    ServerHostsListItemView, serverHostsListTemplate) {
  'use strict';
  var ServerHostsListView = ListView.extend({
    className: 'server-hosts-list',
    template: _.template(serverHostsListTemplate),
    listErrorMsg: 'Failed to load server hosts, ' +
      'server error occurred.',
    initialize: function(options) {
      this.collection = new ServerHostCollection({
        server: options.server.get('id')
      });
      this.listenTo(window.events, 'server_hosts_updated:' +
        options.server.get('id'), this.update);
      this.server = options.server;
      this.serverView = options.serverView;
      ServerHostsListView.__super__.initialize.call(this);
    },
    buildItem: function(model) {
      return new ServerHostsListItemView({
        model: model,
        server: this.server
      });
    },
    resetItems: function(views) {
      if (!views.length) {
        this.$('.no-hosts').slideDown(window.slideTime);
      }
      else {
        this.$('.no-hosts').slideUp(window.slideTime);
      }
      this.serverView.updateHostsCount();
      this.serverView.updateButtons();
    }
  });

  return ServerHostsListView;
});
