define([
  'jquery',
  'underscore',
  'backbone',
  'models/linkRoute',
  'models/linkHost',
  'models/linkHostUri',
  'models/linkHostConf',
  'models/linkPeer',
  'models/linkTransit',
  'views/alert',
  'views/modalAddLocRoute',
  'views/modalAddLocHost',
  'views/modalAddLocPeer',
  'views/modalAddLocTransit',
  'views/modalDeleteLocTransit',
  'views/modalDeleteLocRoute',
  'views/modalModifyLocHost',
  'views/modalLocHostUri',
  'views/modalLocHostConf',
  'views/modalLocHostUbntConf',
  'views/modalDeleteLocHost',
  'views/modalDeleteLocPeer',
  'views/modalModifyLocation',
  'views/modalDeleteLocation',
  'text!templates/linkLocationsListItem.html'
], function($, _, Backbone, LinkRouteModel, LinkHostModel, LinkHostUriModel,
    LinkHostConfModel, LinkPeerModel, LinkTransitModel, AlertView,
    ModalAddLocRouteView, ModalAddLocHostView, ModalAddLocPeerView,
    ModalAddLocTransitView, ModalDeleteLocTransitView,
    ModalDeleteLocRouteView, ModalModifyLocHostView, ModalLocHostUriView,
    ModalLocHostConfView, ModalLocHostUbntConfView, ModalDeleteLocHostView,
    ModalDeleteLocPeerView, ModalModifyLocationView, ModalDeleteLocationView,
    linkLocationsListItemTemplate) {
  'use strict';
  var LinkLocationsListItemView = Backbone.View.extend({
    className: 'link-location',
    template: _.template(linkLocationsListItemTemplate),
    events: {
      'mousedown .location-add-route': 'onAddRoute',
      'mousedown .location-add-host': 'onAddHost',
      'mousedown .location-add-peer': 'onAddPeer',
      'mousedown .link-remove-route': 'onRemoveRoute',
      'mousedown .link-remove-host': 'onRemoveHost',
      'mousedown .link-remove-peer': 'onRemovePeer',
      'mousedown .link-add-transit': 'onAddTransit',
      'mousedown .link-remove-transit': 'onRemoveTransit',
      'mousedown .link-uri-host': 'onHostUri',
      'mousedown .link-conf-host': 'onHostConf',
      'mousedown .link-ubnt-conf-host': 'onHostUbntConf',
      'mousedown .host-name': 'onModifyHost',
      'mousedown .location-settings': 'onSettings',
      'mousedown .location-del': 'onDelete'
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      this.$('[data-toggle="tooltip"]').tooltip();
      return this;
    },
    update: function() {
      this.render();
    },
    getHost: function(hostId) {
      var hosts = this.model.get('hosts');

      for (var i = 0; i < hosts.length; i++) {
        if (hosts[i].id === hostId) {
          return hosts[i];
        }
      }
    },
    onAddRoute: function() {
      var modal = new ModalAddLocRouteView({
        location: this.model.get('id'),
        link: this.model.get('link_id')
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully added location route.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    onAddHost: function() {
      var modal = new ModalAddLocHostView({
        location: this.model.get('id'),
        link: this.model.get('link_id')
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully added location host.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    onAddPeer: function() {
      if (this.collection.length < 2) {
        var alertView = new AlertView({
          type: 'danger',
          message: 'Two locations must be created before creating an peer.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
        return;
      }

      var modal = new ModalAddLocPeerView({
        location: this.model.get('id'),
        link: this.model.get('link_id'),
        locations: this.collection
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully added location peer.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    onRemoveRoute: function(evt) {
      var model = new LinkRouteModel({
        'id': $(evt.currentTarget).attr('data-id'),
        'network': $(evt.currentTarget).attr('data-network'),
        'link_id': this.model.get('link_id'),
        'location_id': this.model.get('id')
      });

      if (evt.shiftKey && evt.ctrlKey && evt.altKey) {
        model.destroy();
        return;
      }

      var modal = new ModalDeleteLocRouteView({
        model: model
      });
      this.addView(modal);
    },
    onRemovePeer: function(evt) {
      var model = new LinkPeerModel({
        'id': $(evt.currentTarget).attr('data-id'),
        'link_id': this.model.get('link_id'),
        'location_id': this.model.get('id'),
        'name': $(evt.currentTarget).attr('data-name')
      });

      if (evt.shiftKey && evt.ctrlKey && evt.altKey) {
        model.destroy();
        return;
      }

      var modal = new ModalDeleteLocPeerView({
        model: model
      });
      this.addView(modal);
    },
    onAddTransit: function(evt) {
      var model = new LinkTransitModel({
        'link_id': this.model.get('link_id'),
        'location_id': this.model.get('id'),
        'transit_id': $(evt.currentTarget).attr('data-id'),
        'name': $(evt.currentTarget).attr('data-name')
      });

      var modal = new ModalAddLocTransitView({
        model: model
      });
      this.addView(modal);
    },
    onRemoveTransit: function(evt) {
      var model = new LinkTransitModel({
        'id': $(evt.currentTarget).attr('data-id'),
        'link_id': this.model.get('link_id'),
        'location_id': this.model.get('id'),
        'name': $(evt.currentTarget).attr('data-name')
      });

      var modal = new ModalDeleteLocTransitView({
        model: model
      });
      this.addView(modal);
    },
    onHostUri: function(evt) {
      var model = new LinkHostUriModel(
        this.getHost($(evt.currentTarget).attr('data-id')));

      var modal = new ModalLocHostUriView({
        model: model
      });
      this.addView(modal);
    },
    onHostConf: function(evt) {
      var model = new LinkHostConfModel(
        this.getHost($(evt.currentTarget).attr('data-id')));

      var modal = new ModalLocHostConfView({
        model: model
      });
      this.addView(modal);
    },
    onHostUbntConf: function(evt) {
      var model = new LinkHostConfModel(
        this.getHost($(evt.currentTarget).attr('data-id')));

      var modal = new ModalLocHostUbntConfView({
        model: model
      });
      this.addView(modal);
    },
    onModifyHost: function(evt) {
      var model = new LinkHostModel(
        this.getHost($(evt.currentTarget).attr('data-id')));

      var modal = new ModalModifyLocHostView({
        model: model
      });
      this.addView(modal);
    },
    onRemoveHost: function(evt) {
      var model = new LinkHostModel(
        this.getHost($(evt.currentTarget).attr('data-id')));

      if (evt.shiftKey && evt.ctrlKey && evt.altKey) {
        model.destroy();
        return;
      }

      var modal = new ModalDeleteLocHostView({
        model: model
      });
      this.addView(modal);
    },
    onSettings: function() {
      var modal = new ModalModifyLocationView({
        model: this.model.clone()
      });
      this.addView(modal);
    },
    onDelete: function(evt) {
      var model = this.model.clone();

      if (evt.shiftKey && evt.ctrlKey && evt.altKey) {
        model.destroy();
        return;
      }

      var modal = new ModalDeleteLocationView({
        model: model
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully deleted link.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    }
  });

  return LinkLocationsListItemView;
});
