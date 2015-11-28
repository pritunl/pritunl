define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalDeleteServer.html'
], function($, _, Backbone, ModalView, modalDeleteServerTemplate) {
  'use strict';
  var ModalDeleteServerView = ModalView.extend({
    className: 'delete-server-modal',
    template: _.template(modalDeleteServerTemplate),
    title: 'Delete Server',
    okText: 'Delete',
    inputMatch: true,
    initialize: function() {
      ModalDeleteServerView.__super__.initialize.call(this);
      this.inputMatchText = this.model.get('name');
    },
    body: function() {
      return this.template();
    },
    onOk: function() {
      this.setLoading('Deleting server...');
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

  return ModalDeleteServerView;
});
