define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalDeleteLocExclude.html'
], function($, _, Backbone, ModalView, AlertView,
    modalDeleteLocExcludeTemplate) {
  'use strict';
  var ModalDeleteLocExcludeView = ModalView.extend({
    className: 'delete-location-exclude-modal',
    template: _.template(modalDeleteLocExcludeTemplate),
    title: 'Remove Location Exclude',
    okText: 'Remove',
    body: function() {
      return this.template(this.model.toJSON());
    },
    onOk: function() {
      this.setLoading('Removing location exclude...');
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

  return ModalDeleteLocExcludeView;
});
