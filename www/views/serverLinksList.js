define([
  'jquery',
  'underscore',
  'backbone',
  'collections/serverLink',
  'views/list',
  'views/serverLinksListItem',
  'text!templates/serverLinksList.html'
], function($, _, Backbone, ServerLinkCollection, ListView,
    ServerLinksListItemView, serverLinksListTemplate) {
  'use strict';
  var ServerLinksListView = ListView.extend({
    className: 'server-links-list',
    template: _.template(serverLinksListTemplate),
    listErrorMsg: 'Failed to load server links, ' +
      'server error occurred.',
    initialize: function(options) {
      this.collection = new ServerLinkCollection({
        server: options.server.get('id')
      });
      this.listenTo(window.events, 'server_links_updated:' +
        options.server.get('id'), this.update);
      this.server = options.server;
      this.serverView = options.serverView;
      ServerLinksListView.__super__.initialize.call(this);
    },
    buildItem: function(model) {
      var modelView = new ServerLinksListItemView({
        model: model,
        server: this.server
      });
      return modelView;
    },
    resetItems: function(views) {
      if (!views.length) {
        this.$el.addClass('no-links');
      }
      else {
        this.$el.removeClass('no-links');
      }
      this.serverView.updateButtons();
    }
  });

  return ServerLinksListView;
});
