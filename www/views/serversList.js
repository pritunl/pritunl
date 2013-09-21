define([
  'jquery',
  'underscore',
  'backbone',
  'collections/server',
  'views/list',
  'views/alert',
  'views/serversListItem',
  'views/modalAddServer',
  'text!templates/serversList.html'
], function($, _, Backbone, ServerCollection, ListView, AlertView,
    ServersListItemView, ModalAddServerView, serversListTemplate) {
  'use strict';
  var ServersListView = ListView.extend({
    className: 'servers-list',
    listContainer: '.servers-list-container',
    template: _.template(serversListTemplate),
    events: {
      'click .servers-add-server': 'onAddServer'
    },
    initialize: function() {
      this.collection = new ServerCollection();
      ServersListView.__super__.initialize.call(this);
    },
    update: function() {
      this.collection.reset([
        {
          'id': '1',
          'name': 'server0',
          'status': 'online',
          'uptime': '1024d 12h 32m 15s',
          'users_online': 12,
          'users_total': 128,
          'network': '10.232.128.0/24',
          'interface': 'tun0',
          'port': '12345',
          'protocol': 'udp',
          'local_network': null
        },
        {
          'id': '2',
          'name': 'server1',
          'status': 'offline',
          'uptime': '-',
          'users_online': 0,
          'users_total': 12,
          'network': '10.64.32.0/16',
          'interface': 'tun1',
          'port': '4563',
          'protocol': 'tcp',
          'local_network': '10.0.0.0'
        }
      ]);
    },
    onAddServer: function() {
      var modal = new ModalAddServerView();
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'warning',
          message: 'Successfully added server.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
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
