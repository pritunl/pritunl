define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalDeleteHost.html'
], function($, _, Backbone, ModalView, AlertView, modalDeleteOrgTemplate) {
  'use strict';
  var ModalDeleteHostView = ModalView.extend({
    className: 'delete-host-modal',
    template: _.template(modalDeleteOrgTemplate),
    title: 'Delete Host',
    okText: 'Delete',
    inputMatch: true,
    initialize: function() {
      ModalDeleteHostView.__super__.initialize.call(this);
      this.inputMatchText = this.model.get('name');
    },
    body: function() {
      return this.template();
    },
    onOk: function() {
      this.setLoading('Deleting host...');
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

  return ModalDeleteHostView;
});
