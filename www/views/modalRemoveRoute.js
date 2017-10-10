define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalRemoveRoute.html'
], function($, _, Backbone, ModalView, AlertView, modalRemoveRouteTemplate) {
  'use strict';
  var ModalRemoveRouteView = ModalView.extend({
    className: 'remove-route-modal',
    template: _.template(modalRemoveRouteTemplate),
    title: 'Remove Route',
    okText: 'Remove',
    body: function() {
      return this.template(this.model.toJSON());
    },
    onOk: function() {
      this.setLoading('Removing route...');
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

  return ModalRemoveRouteView;
});
