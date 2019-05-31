define([
  'jquery',
  'underscore',
  'backbone',
  'views/alert',
  'views/modalModifyRoute',
  'views/modalRemoveRoute',
  'text!templates/serverRoutesListItem.html'
], function($, _, Backbone, AlertView, ModalModifyRouteView,
    ModalRemoveRouteView, serverRoutesListItemTemplate) {
  'use strict';
  var ServerRoutesListItemView = Backbone.View.extend({
    className: 'route',
    template: _.template(serverRoutesListItemTemplate),
    events: {
      'click .route-network': 'onModify',
      'click .server-remove-route': 'onRemove'
    },
    initialize: function(options) {
      this.server = options.server;
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      this.$('[data-toggle="tooltip"]').tooltip();
      return this;
    },
    update: function() {
      this.$('.route-network').text(this.model.get('network'));
      this.$('.route-comment').text(this.model.get('comment'));
      this.$('.route-network-no-click').text(this.model.get('network'));

      if (this.model.get('advertise') || this.model.get('vpc_id')) {
        this.$('.route-vpc-id').text('Cloud Advertise');
        this.$('.route-vpc-id').show();
      } else {
        this.$('.route-vpc-id').hide();
      }
      if (this.model.get('virtual_network')) {
        this.$('.route-virtual-network').show();
      } else {
        this.$('.route-virtual-network').hide();
      }
      if (this.model.get('network_link')) {
        this.$('.route-network-link').show();
      } else {
        this.$('.route-network-link').hide();
      }
      if (this.model.get('server_link')) {
        this.$('.route-server-link').show();
      } else {
        this.$('.route-server-link').hide();
      }
      if (this.model.get('nat') && !this.model.get('net_gateway') &&
          !this.model.get('nat_netmap')) {
        this.$('.route-nat').show();
      } else {
        this.$('.route-nat').hide();
      }
      if (this.model.get('nat') && !this.model.get('net_gateway') &&
          this.model.get('nat_netmap')) {
        this.$('.route-nat-netmap').show();
      } else {
        this.$('.route-nat-netmap').hide();
      }
      if (this.model.get('net_gateway')) {
        this.$('.route-net-gateway').show();
      } else {
        this.$('.route-net-gateway').hide();
      }

      if (this.model.get('network') === '::/0' ||
          this.model.get('virtual_network') ||
          this.model.get('network_link') ||
          this.model.get('server_link')) {
        this.$('.server-remove-route').attr('disabled', 'disabled');
      } else {
        this.$('.server-remove-route').removeAttr('disabled');
      }
    },
    onModify: function() {
      var model = this.model.clone();

      var modal = new ModalModifyRouteView({
        model: model
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully modified route.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    onRemove: function(evt) {
      var model = this.model.clone();

      if (evt.shiftKey && evt.ctrlKey && evt.altKey) {
        model.destroy();
        return;
      }

      var modal = new ModalRemoveRouteView({
        model: model
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully removed route.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    }
  });

  return ServerRoutesListItemView;
});
