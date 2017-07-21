define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalDeleteLocHost.html'
], function($, _, Backbone, ModalView, AlertView,
    modalDeleteLocHostTemplate) {
  'use strict';
  var ModalDeleteLocHostView = ModalView.extend({
    className: 'delete-location-host-modal',
    template: _.template(modalDeleteLocHostTemplate),
    title: 'Remove Location Host',
    okText: 'Remove',
    body: function() {
      return this.template(this.model.toJSON());
    },
    onOk: function() {
      this.setLoading('Removing location host...');
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

  return ModalDeleteLocHostView;
});
