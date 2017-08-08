define([
  'jquery',
  'underscore',
  'backbone',
  'models/linkRoute',
  'models/linkHost',
  'models/linkHostUri',
  'models/linkExclude',
  'views/alert',
  'views/modalAddLocRoute',
  'views/modalAddLocHost',
  'views/modalAddLocExclude',
  'views/modalDeleteLocRoute',
  'views/modalModifyLocHost',
  'views/modalLocHostUri',
  'views/modalDeleteLocHost',
  'views/modalDeleteLocExclude',
  'views/modalModifyLocation',
  'views/modalDeleteLocation',
  'text!templates/linkLocationsListItem.html'
], function($, _, Backbone, LinkRouteModel, LinkHostModel, LinkHostUriModel,
    LinkExcludeModel, AlertView, ModalAddLocRouteView, ModalAddLocHostView,
    ModalAddLocExcludeView, ModalDeleteLocRouteView, ModalModifyLocHostView,
    ModalLocHostUriView, ModalDeleteLocHostView, ModalDeleteLocExcludeView,
    ModalModifyLocationView, ModalDeleteLocationView,
    linkLocationsListItemTemplate) {
  'use strict';
  var LinkLocationsListItemView = Backbone.View.extend({
    className: 'link-location',
    template: _.template(linkLocationsListItemTemplate),
    events: {
      'mousedown .location-add-route': 'onAddRoute',
      'mousedown .location-add-host': 'onAddHost',
      'mousedown .location-add-exclude': 'onAddExclude',
      'mousedown .link-remove-route': 'onRemoveRoute',
      'mousedown .link-remove-host': 'onRemoveHost',
      'mousedown .link-remove-exclude': 'onRemoveExclude',
      'mousedown .link-uri-host': 'onHostUri',
      'mousedown .host-name': 'onModifyHost',
      'mousedown .location-settings': 'onSettings',
      'mousedown .location-del': 'onDelete'
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
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
    onAddExclude: function() {
      if (this.collection.length < 2) {
        var alertView = new AlertView({
          type: 'danger',
          message: 'Two locations must be created before creating an exclude.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
        return;
      }

      var modal = new ModalAddLocExcludeView({
        location: this.model.get('id'),
        link: this.model.get('link_id'),
        locations: this.collection
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully added location exclude.',
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
    onRemoveExclude: function(evt) {
      var model = new LinkExcludeModel({
        'id': $(evt.currentTarget).attr('data-id'),
        'link_id': this.model.get('link_id'),
        'location_id': this.model.get('id')
      });

      if (evt.shiftKey && evt.ctrlKey && evt.altKey) {
        model.destroy();
        return;
      }

      var modal = new ModalDeleteLocExcludeView({
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
