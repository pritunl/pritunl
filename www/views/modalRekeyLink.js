define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalRekeyLink.html'
], function($, _, Backbone, ModalView, AlertView, modalRekeyLinkTemplate) {
  'use strict';
  var ModalRekeyLinkView = ModalView.extend({
    className: 'rekey-link-modal',
    template: _.template(modalRekeyLinkTemplate),
    title: 'Rekey Link',
    okText: 'Rekey',
    body: function() {
      return this.template(this.model.toJSON());
    },
    onOk: function() {
      this.setLoading('Rekeying link...');
      this.model.save({
        key: true
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

  return ModalRekeyLinkView;
});
