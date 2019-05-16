define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalDeleteLocTransit.html'
], function($, _, Backbone, ModalView, AlertView,
    modalDeleteLocTransitTemplate) {
  'use strict';
  var ModalDeleteLocTransitView = ModalView.extend({
    className: 'delete-location-transit-modal',
    template: _.template(modalDeleteLocTransitTemplate),
    title: 'Disable Peer Transit',
    okText: 'Disable',
    body: function() {
      return this.template(this.model.toJSON());
    },
    onOk: function() {
      this.setLoading('Disabling location transit...');
      this.model.destroy({
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

  return ModalDeleteLocTransitView;
});
