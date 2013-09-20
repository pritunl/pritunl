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
          'uptime': '128 days 12 hrs 34 mins',
          'users_online': 12,
          'users_total': 32,
          'network': '10.232.128.0/24',
          'interface': 'tun0',
          'port': '12345/udp'
        },
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
