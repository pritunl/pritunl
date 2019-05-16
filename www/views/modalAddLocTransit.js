define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalAddLocTransit.html'
], function($, _, Backbone, ModalView, AlertView,
    modalAddLocTransitTemplate) {
  'use strict';
  var ModalAddLocTransitView = ModalView.extend({
    className: 'add-location-transit-modal',
    template: _.template(modalAddLocTransitTemplate),
    title: 'Enable Peer Transit',
    okText: 'Enable',
    body: function() {
      return this.template(this.model.toJSON());
    },
    onOk: function() {
      this.setLoading('Enabling location transit...');
      this.model.save({}, {
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

  return ModalAddLocTransitView;
});
