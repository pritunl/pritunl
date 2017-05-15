define([
  'jquery',
  'underscore',
  'backbone',
  'models/linkRoute',
  'models/linkHost',
  'views/alert',
  'views/modalAddLocRoute',
  'views/modalAddLocHost',
  'views/modalDeleteLocRoute',
  'views/modalDeleteLocHost',
  'views/modalModifyLocation',
  'views/modalDeleteLocation',
  'text!templates/linkLocationsListItem.html'
], function($, _, Backbone, LinkRouteModel, LinkHostModel, AlertView,
    ModalAddLocRouteView, ModalAddLocHostView, ModalDeleteLocRouteView,
    ModalDeleteLocHostView, ModalModifyLocationView,
    ModalDeleteLocationView, linkLocationsListItemTemplate) {
  'use strict';
  var LinkLocationsListItemView = Backbone.View.extend({
    className: 'link-location',
    template: _.template(linkLocationsListItemTemplate),
    events: {
      'click .location-add-route': 'onAddRoute',
      'click .location-add-host': 'onAddHost',
      'click .link-remove-route': 'onRemoveRoute',
      'click .link-remove-host': 'onRemoveHost',
      'click .location-settings': 'onSettings',
      'click .location-del': 'onDelete'
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    },
    update: function() {
      this.render();
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
    onRemoveRoute: function(evt) {
      var model = new LinkRouteModel({
        'id': $(evt.currentTarget).attr('data-id'),
        'network': $(evt.currentTarget).attr('data-network'),
        'link_id': this.model.get('link_id'),
        'location_id': this.model.get('id')
      });

      var modal = new ModalDeleteLocRouteView({
        model: model
      });
      this.addView(modal);
    },
    onRemoveHost: function(evt) {
      var model = new LinkHostModel({
        'id': $(evt.currentTarget).attr('data-id'),
        'name': $(evt.currentTarget).attr('data-name'),
        'link_id': this.model.get('link_id'),
        'location_id': this.model.get('id')
      });

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

      if (evt.shiftKey && evt.ctrlKey) {
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
