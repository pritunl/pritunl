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
      this.orgs = new OrgCollection();
      this.hosts = new HostCollection();
      this.statusModel = new StatusModel();
      this.listenTo(window.events, 'servers_updated', this.update);
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
    onAddServer: function() {
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
      var modal = new ModalAddRouteView({
        collection: this.collection
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
        this.$('.servers-attach-org').attr('disabled', 'disabled');
        this.$('.servers-attach-host').attr('disabled', 'disabled');
        this.$('.servers-link-server').attr('disabled', 'disabled');
        this.$('.no-servers').slideDown(window.slideTime);
      }
      else {
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
