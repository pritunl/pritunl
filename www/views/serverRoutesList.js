define([
  'jquery',
  'underscore',
  'backbone',
  'collections/serverRoute',
  'views/list',
  'views/serverRoutesListItem',
  'text!templates/serverRoutesList.html'
], function($, _, Backbone, ServerRouteCollection, ListView,
    ServerRoutesListItemView, serverRoutesListTemplate) {
  'use strict';
  var ServerRoutesListView = ListView.extend({
    className: 'server-routes-list',
    template: _.template(serverRoutesListTemplate),
    listErrorMsg: 'Failed to load server routes, ' +
      'server error occurred.',
    initialize: function(options) {
      this.collection = new ServerRouteCollection({
        server: options.server.get('id')
      });
      this.listenTo(window.events, 'server_routes_updated:' +
        options.server.get('id'), this.update);
      this.server = options.server;
      this.serverView = options.serverView;
      ServerRoutesListView.__super__.initialize.call(this);
    },
    buildItem: function(model) {
      return new ServerRoutesListItemView({
        model: model,
        server: this.server
      });
    }
  });

  return ServerRoutesListView;
});
