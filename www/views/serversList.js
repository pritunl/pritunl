define([
  'jquery',
  'underscore',
  'backbone',
  'models/status',
  'collections/server',
  'collections/org',
  'collections/host',
  'views/list',
  'views/alert',
  'views/serversListItem',
  'views/modalAddServer',
  'views/modalAttachOrg',
  'views/modalAttachHost',
  'views/modalAttachLink',
  'text!templates/serversList.html'
], function($, _, Backbone, StatusModel, ServerCollection, OrgCollection,
    HostCollection, ListView, AlertView, ServersListItemView,
    ModalAddServerView, ModalAttachOrgView, ModalAttachHostView,
    ModalAttachLinkView, serversListTemplate) {
  'use strict';
  var ServersListView = ListView.extend({
    className: 'servers-list',
    listContainer: '.servers-list-container',
    template: _.template(serversListTemplate),
    listErrorMsg: 'Failed to load servers, server error occurred.',
    events: {
      'click .servers-add-server': 'onAddServer',
      'click .servers-attach-org': 'onAttachOrg',
      'click .servers-attach-host': 'onAttachHost',
      'click .servers-link-server': 'onLinkServer'
    },
    initialize: function() {
      this.collection = new ServerCollection();
      this.orgs = new OrgCollection();
      this.statusModel = new StatusModel();
      this.listenTo(window.events, 'servers_updated', this.update);
      this.listenTo(window.events, 'organizations_updated', this.updateOrgs);
      this.listenTo(window.events, 'hosts_updated', this.updateHosts);
      ServersListView.__super__.initialize.call(this);
    },
    updateOrgs: function() {
      this.orgs.fetch({
        error: function() {
          this.orgs.reset();
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to load organizations, server error occurred.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
        }.bind(this)
      });
    },
    updateLinks: function() {
      this.links.fetch({
        error: function() {
          this.links.reset();
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to load links, server error occurred.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
        }.bind(this)
      });
    },
    _addServer: function(type) {
      this.$('.servers-add-server').attr('disabled', 'disabled');
      this.statusModel.fetch({
        success: function() {
          var i;
          var usedNetworks = [];
          var usedPorts = [];
          var usedInterfaces = [];
          for (i = 0; i < this.collection.models.length; i++) {
            usedNetworks.push(this.collection.models[i].get('network'));
            usedPorts.push(this.collection.models[i].get('port'));
            usedInterfaces.push(this.collection.models[i].get('interface'));
          }

          var modal = new ModalAddServerView({
            type: type,
            publicIp: this.statusModel.get('public_ip'),
            localNetworks: this.statusModel.get('local_networks'),
            usedNetworks: usedNetworks,
            usedPorts: usedPorts,
            usedInterfaces: usedInterfaces
          });
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
          this.$('.servers-add-server').removeAttr('disabled');
        }.bind(this),
        error: function() {
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to load server information, ' +
              'server error occurred.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
          this.$('.servers-add-server').removeAttr('disabled');
        }.bind(this)
      });
    },
    onAddServer: function() {
      this._addServer('server');
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
      if (!this.orgs.length) {
        var alertView = new AlertView({
          type: 'danger',
          message: 'No organizations exists, an organization must be ' +
            'created before attaching.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
        return;
      }
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
    onAttachHost: function() {
      if (this.hosts.models.length) {
        this._attachHost();
        return;
      }
      this.$('.servers-attach-host').attr('disabled', 'disabled');
      this.hosts.fetch({
        success: function() {
          this._attachHost();
          this.$('.servers-attach-host').removeAttr('disabled');
        }.bind(this),
        error: function() {
          this.hosts.reset();
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to load hosts, server error occurred.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
          this.$('.servers-attach-host').removeAttr('disabled');
        }.bind(this)
      });
    },
    _attachHost: function() {
      if (!this.hosts.length) {
        var alertView = new AlertView({
          type: 'danger',
          message: 'No hosts exists, a host must be created before attaching.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
        return;
      }
      var modal = new ModalAttachHostView({
        hosts: this.hosts,
        collection: this.collection
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'warning',
          message: 'Successfully attached host.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    onLinkServer: function() {
      console.log('test')
      if (this.collection.length < 2) {
        var alertView = new AlertView({
          type: 'danger',
          message: 'No servers exists, a server must be created before ' +
            'attaching.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
        return;
      }

      var modal = new ModalAttachLinkView({
        collection: this.collection
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'warning',
          message: 'Successfully linked server.',
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
        this.$('.servers-attach-host').attr('disabled', 'disabled');
        this.$('.no-servers').slideDown(window.slideTime);
      }
      else {
        this.$('.servers-attach-org').removeAttr('disabled');
        this.$('.servers-attach-host').removeAttr('disabled');
        this.$('.no-servers').slideUp(window.slideTime);
      }
    }
  });

  return ServersListView;
});
