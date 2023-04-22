define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalDeleteUserDevice.html'
], function($, _, Backbone, ModalView, AlertView,
    modalDeleteUserDeviceTemplate) {
  'use strict';
  var ModalDeleteUserDevice = ModalView.extend({
    className: 'delete-user-device-modal',
    template: _.template(modalDeleteUserDeviceTemplate),
    title: 'Remove User Device',
    okText: 'Remove',
    body: function() {
      return this.template(this.model.toJSON());
    },
    onOk: function() {
      this.setLoading('Removing user device...');
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

  return ModalDeleteUserDevice;
});
