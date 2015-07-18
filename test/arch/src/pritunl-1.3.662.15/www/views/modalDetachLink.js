define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalDetachLink.html'
], function($, _, Backbone, ModalView, AlertView, modalDetachLinkTemplate) {
  'use strict';
  var ModalDetachLinkView = ModalView.extend({
    className: 'detach-link-modal',
    template: _.template(modalDetachLinkTemplate),
    title: 'Detach Link',
    okText: 'Detach',
    body: function() {
      return this.template(this.model.toJSON());
    },
    onOk: function() {
      this.setLoading('Detaching link...');
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
            this.setAlert('danger',
            'Failed to detach link, server error occurred.');
          }
        }.bind(this)
      });
    }
  });

  return ModalDetachLinkView;
});
