define([
  'jquery',
  'underscore',
  'backbone',
  'collections/server',
  'collections/org',
  'views/list',
  'views/alert',
  'views/serversListItem',
  'views/modalAddServer',
  'views/modalAttachOrg',
  'text!templates/serversList.html'
], function($, _, Backbone, ServerCollection, OrgCollection, ListView,
    AlertView, ServersListItemView, ModalAddServerView, ModalAttachOrgView,
    serversListTemplate) {
  'use strict';
  var ServersListView = ListView.extend({
    className: 'servers-list',
    listContainer: '.servers-list-container',
    template: _.template(serversListTemplate),
    listErrorMsg: 'Failed to load servers, server error occurred.',
    events: {
      'click .servers-add-server': 'onAddServer',
      'click .servers-attach-org': 'onAttachOrg'
    },
    initialize: function() {
      this.collection = new ServerCollection();
      this.orgs = new OrgCollection();
      this.listenTo(window.events, 'servers_updated', this.update);
      this.listenTo(window.events, 'organizations_updated', this.updateOrgs);
      ServersListView.__super__.initialize.call(this);
    },
    update: function() {
      this.collection.reset([
        {
          'id': 'b4182ab869ff4269b4015391e618e4a8',
          'name': 'server0',
          'status': 'online',
          'uptime': 88488573,
          'users_online': 12,
          'users_total': 128,
          'network': '10.232.128.0/24',
          'interface': 'tun0',
          'port': '12345',
          'protocol': 'udp',
          'local_network': null
        },
        {
          'id': '65a3224e94ad4449aacac992d4e1e6ab',
          'name': 'server1',
          'status': 'offline',
          'uptime': null,
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
    updateOrgs: function() {
      this.collection.fetch({
        error: function() {
          this.collection.reset();
        }.bind(this)
      });
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
    onAttachOrg: function() {
      if (this.orgs.models.length) {
        this._attachOrg();
        return;
      }
      this.$('.servers-attach-org').attr('disabled', 'disabled');
      this.orgs.fetch({
        success: function() {
          this._attachOrg();
          this.$('.servers-attach-org').removeAttr('disabled');
        }.bind(this),
        error: function() {
          this.orgs.reset();
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to load organizations, server error occurred.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
          this.$('.servers-attach-org').removeAttr('disabled');
        }.bind(this)
      });
    },
    _attachOrg: function() {
      var modal = new ModalAttachOrgView({
        orgs: this.orgs,
        collection: this.collection
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'warning',
          message: 'Successfully attached organization.',
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
