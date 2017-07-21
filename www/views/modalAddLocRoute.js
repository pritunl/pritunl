define([
  'jquery',
  'underscore',
  'backbone',
  'models/linkRoute',
  'views/modal',
  'text!templates/modalAddLocRoute.html'
], function($, _, Backbone, LinkRouteModel, ModalView,
    modalAddLocRouteTemplate) {
  'use strict';
  var ModalAddLocRouteView = ModalView.extend({
    className: 'add-location-route-modal',
    template: _.template(modalAddLocRouteTemplate),
    title: 'Add Location Route',
    okText: 'Add',
    initialize: function(options) {
      this.link = options.link;
      this.location = options.location;
      ModalAddLocRouteView.__super__.initialize.call(this);
    },
    body: function() {
      return this.template();
    },
    onOk: function() {
      var network = this.$('.network input').val();

      if (!network) {
        this.setAlert('danger', 'Network can not be empty.', '.name');
        return;
      }

      this.setLoading('Adding location route...');
      var model = new LinkRouteModel();
      model.save({
        link_id: this.link,
        location_id: this.location,
        network: network
      }, {
        success: function() {
          this.close(true);
        }.bind(this),
        error: function(model, response) {
          this.clearLoading();
          if (response.responseJSON) {
            this.setAlert('danger', response.responseJSON.error_msg);
          }
          else {
            this.setAlert('danger', this.errorMsg);
          }
        }.bind(this)
      });
    }
  });

  return ModalAddLocRouteView;
});
