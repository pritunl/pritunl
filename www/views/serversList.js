define([
  'jquery',
  'underscore',
  'backbone',
  'collections/server',
  'views/list',
  'views/serversListItem',
  'text!templates/serversList.html'
], function($, _, Backbone, ServerCollection, ListView, ServersListItemView,
    serversListTemplate) {
  'use strict';
  var ServersListView = ListView.extend({
    className: 'servers-list',
    listContainer: '.servers-list-container',
    template: _.template(serversListTemplate),
    init: function() {
      this.collection = new ServerCollection();
    },
    update: function() {
      this.collection.reset([
        {
          'id': '1',
          'name': 'server0',
          'status': 'online',
          'uptime': '1024d 12h 32m 15s',
          'users_online': 12,
          'users_total': 32,
          'network': '10.232.128.0/24',
          'interface': 'tun0',
          'port': '12345/udp'
        },
        {
          'id': '2',
          'name': 'server1',
          'status': 'offline',
          'uptime': '43d 14h 50m 32s',
          'users_online': 8,
          'users_total': 12,
          'network': '10.64.32.0/16',
          'interface': 'tun1',
          'port': '4563/tcp'
        }
      ]);
    },
    buildItem: function(model) {
      var modelView = new ServersListItemView({
        model: model
      });
      this.listenTo(modelView, 'select', this.onSelect);
      return modelView;
    },
    resetItems: function(views) {
      if (!views.length) {
        this.$('.servers-attach-org').attr('disabled', 'disabled');
        this.$('.no-servers').slideDown(250);
      }
      else {
        this.$('.servers-attach-org').removeAttr('disabled');
        this.$('.no-servers').slideUp(250);
      }
    }
  });

  return ServersListView;
});
