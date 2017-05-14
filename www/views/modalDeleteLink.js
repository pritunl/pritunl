define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalDeleteLink.html'
], function($, _, Backbone, ModalView, AlertView, modalDeleteLinkTemplate) {
  'use strict';
  var ModalDeleteLinkView = ModalView.extend({
    className: 'delete-link-modal',
    template: _.template(modalDeleteLinkTemplate),
    title: 'Delete Link',
    okText: 'Delete',
    inputMatch: true,
    initialize: function() {
      ModalDeleteLinkView.__super__.initialize.call(this);
      this.inputMatchText = this.model.get('name');
    },
    body: function() {
      return this.template();
    },
    onOk: function() {
      this.setLoading('Deleting link...');
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

  return ModalDeleteLinkView;
});
