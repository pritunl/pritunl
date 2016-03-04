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
      this.$('.route-network-no-click').text(this.model.get('network'));
      if (this.model.get('nat')) {
        this.$('.route-nat').show();
      } else {
        this.$('.route-nat').hide();
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

      if (evt.shiftKey && evt.ctrlKey) {
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
