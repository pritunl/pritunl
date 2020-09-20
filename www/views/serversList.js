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
  'views/modalAddRoute',
  'views/modalAttachOrg',
  'views/modalAttachHost',
  'views/modalAttachLink',
  'text!templates/serversList.html'
], function($, _, Backbone, StatusModel, ServerCollection, OrgCollection,
    HostCollection, ListView, AlertView, ServersListItemView,
    ModalAddServerView, ModalAddRouteView, ModalAttachOrgView,
    ModalAttachHostView, ModalAttachLinkView, serversListTemplate) {
  'use strict';
  var ServersListView = ListView.extend({
    className: 'servers-list',
    listContainer: '.servers-list-container',
    template: _.template(serversListTemplate),
    listErrorMsg: 'Failed to load servers, server error occurred.',
    events: {
      'click .prev-page': 'prevPage',
      'click .next-page': 'nextPage',
      'click .link.first': 'firstPage',
      'click .link.last': 'lastPage',
      'click .servers-add-server': 'onAddServer',
      'click .servers-add-route': 'onAddRoute',
      'click .servers-attach-org': 'onAttachOrg',
      'click .servers-attach-host': 'onAttachHost',
      'click .servers-link-server': 'onLinkServer'
    },
    initialize: function() {
      this.collection = new ServerCollection();
      this.servers = new ServerCollection();
      this.orgs = new OrgCollection();
      this.hosts = new HostCollection();
      this.statusModel = new StatusModel();
      this.listenTo(window.events, 'servers_updated', this.update);
      this.listenTo(window.events, 'servers_updated', this.updateServers);
      this.listenTo(window.events, 'organizations_updated', this.updateOrgs);
      this.listenTo(window.events, 'hosts_updated', this.updateHosts);
      ServersListView.__super__.initialize.call(this);
    },
    prevPage: function() {
      this.collection.prevPage();
      this.update();
    },
    nextPage: function() {
      this.collection.nextPage();
      this.update();
    },
    firstPage: function() {
      this.collection.setPage(0);
      this.update();
    },
    lastPage: function() {
      this.collection.setPage(this.collection.getPageTotal());
      this.update();
    },
    updateServers: function(callback) {
      this.servers.fetch({
        success: function() {
          if (callback) {
            callback();
          }
        }.bind(this),
        error: function() {
          this.servers.reset();
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to load servers, server error occurred.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
          if (callback) {
            callback();
          }
        }.bind(this)
      });
    },
    updateOrgs: function(callback) {
      this.orgs.fetch({
        success: function() {
          if (callback) {
            callback();
          }
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
          if (callback) {
            callback();
          }
        }.bind(this)
      });
    },
    updateHosts: function(callback) {
      this.hosts.fetch({
        success: function() {
          if (callback) {
            callback();
          }
        }.bind(this),
        error: function() {
          this.links.reset();
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to load hosts, server error occurred.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
          if (callback) {
            callback();
          }
        }.bind(this)
      });
    },
    onAddServer: function() {
      if (!this.servers.models.length) {
        this.updateServers((this._addServer).bind(this));
      } else {
        this._addServer();
      }
    },
    _addServer: function() {
      this.$('.servers-add-server').attr('disabled', 'disabled');
      this.statusModel.fetch({
        success: function() {
          var i;
          var usedNetworks = [];
          var usedPorts = [];
          var usedInterfaces = [];
          for (i = 0; i < this.servers.models.length; i++) {
            usedNetworks.push(this.servers.models[i].get('network'));
            usedPorts.push(this.servers.models[i].get('port'));
            usedInterfaces.push(this.servers.models[i].get('interface'));
          }

          var modal = new ModalAddServerView({
            publicIp: this.statusModel.get('public_ip'),
            localNetworks: this.statusModel.get('local_networks'),
            usedNetworks: usedNetworks,
            usedPorts: usedPorts,
            usedInterfaces: usedInterfaces
          });
          this.listenToOnce(modal, 'applied', function() {
            var alertView = new AlertView({
              type: 'success',
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
    onAddRoute: function() {
      if (!this.servers.models.length) {
        this.updateServers((this._addRoute).bind(this));
      } else {
        this._addRoute();
      }
    },
    _addRoute: function() {
      var modal = new ModalAddRouteView({
        collection: this.servers
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully added route.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    onAttachOrg: function() {
      var callback = function() {
        if (!this.orgs.models.length) {
          this.updateOrgs((this._attachOrg).bind(this));
        } else {
          this._attachOrg();
        }
      }.bind(this);

      if (!this.servers.models.length) {
        this.updateServers(callback);
      } else {
        callback();
      }
    },
    _attachOrg: function() {
      if (!this.orgs.length) {
        var alertView = new AlertView({
          type: 'danger',
          message: 'No organizations exist, an organization must be ' +
            'created before attaching.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
        return;
      }
      var modal = new ModalAttachOrgView({
        orgs: this.orgs,
        collection: this.servers
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully attached organization.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    onAttachHost: function() {
      var callback = function() {
        if (!this.hosts.models.length) {
          this.updateHosts((this._attachHost).bind(this));
        } else {
          this._attachHost();
        }
      }.bind(this);

      if (!this.servers.models.length) {
        this.updateServers(callback);
      } else {
        callback();
      }
    },
    _attachHost: function() {
      if (!this.hosts.length) {
        var alertView = new AlertView({
          type: 'danger',
          message: 'No hosts exist, a host must be created before attaching.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
        return;
      }
      var modal = new ModalAttachHostView({
        hosts: this.hosts,
        collection: this.servers
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully attached host.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    onLinkServer: function() {
      if (!this.servers.models.length) {
        this.updateServers((this._linkServer).bind(this));
      } else {
        this._linkServer();
      }
    },
    _linkServer: function() {
      if (this.servers.length < 2) {
        var alertView = new AlertView({
          type: 'danger',
          message: 'Two servers must be created before creating a link.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
        return;
      }

      var modal = new ModalAttachLinkView({
        collection: this.servers
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
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
    getOptions: function() {
      return {
        'page': this.collection.getPage()
      };
    },
    addPageElem: function(page, curPage) {
      var pageElem = $('<a class="link page">' + (page + 1) + '</a>');
      this.$('.pages .link.last').before(pageElem);
      if (page === curPage) {
        pageElem.addClass('current');
      }
      pageElem.one('click', function() {
        this.collection.setPage(page);
        this.update();
      }.bind(this));
    },
    resetItems: function(views) {
      var curPage = this.collection.getPage();
      var pageTotal = this.collection.getPageTotal();

      if (!views.length) {
        this.$('.servers-add-route').attr('disabled', 'disabled');
        this.$('.servers-attach-org').attr('disabled', 'disabled');
        this.$('.servers-attach-host').attr('disabled', 'disabled');
        this.$('.servers-link-server').attr('disabled', 'disabled');
        this.$('.no-servers').slideDown(window.slideTime);
      }
      else {
        this.$('.servers-add-route').removeAttr('disabled');
        this.$('.servers-attach-org').removeAttr('disabled');
        this.$('.servers-attach-host').removeAttr('disabled');
        this.$('.servers-link-server').removeAttr('disabled');
        this.$('.no-servers').slideUp(window.slideTime);
      }

      if (!this.collection.getPage()) {
        this.$('.pages').addClass('padded-left');
        this.$('.prev-page').hide();
      }
      else {
        this.$('.pages').removeClass('padded-left');
        this.$('.prev-page').show();
      }
      if (this.collection.isLastPage()) {
        this.$('.pages').addClass('padded-right');
        this.$('.next-page').hide();
      }
      else {
        this.$('.pages').removeClass('padded-right');
        this.$('.next-page').show();
      }

      if (pageTotal < 2) {
        this.$('.pages').hide();
      }
      else{
        this.$('.pages').show();
        var i;
        var page = Math.max(0, curPage - 7);
        this.$('.pages .link.page').remove();
        this.$('.pages .link.first').removeClass('current');
        this.$('.pages .link.last').removeClass('current');
        for (i = 0; i < 15; i++) {
          if (page > 0) {
            this.addPageElem(page, curPage);
          }
          page += 1;
          if (page > pageTotal - 1) {
            break;
          }
        }
        if (curPage === 0) {
          this.$('.pages .link.first').addClass('current');
        }
        else if (curPage === pageTotal) {
          this.$('.pages .link.last').addClass('current');
        }
      }
    }
  });

  return ServersListView;
});
