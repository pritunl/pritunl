define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalDeleteLocRoute.html'
], function($, _, Backbone, ModalView, AlertView,
    modalDeleteLocRouteTemplate) {
  'use strict';
  var ModalDeleteLocRouteView = ModalView.extend({
    className: 'delete-location-route-modal',
    template: _.template(modalDeleteLocRouteTemplate),
    title: 'Remove Location Route',
    okText: 'Remove',
    body: function() {
      return this.template(this.model.toJSON());
    },
    onOk: function() {
      this.setLoading('Removing location route...');
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

  return ModalDeleteLocRouteView;
});
