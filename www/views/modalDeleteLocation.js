define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalDeleteLocation.html'
], function($, _, Backbone, ModalView, AlertView,
    modalDeleteLocationTemplate) {
  'use strict';
  var ModalDeleteLocationView = ModalView.extend({
    className: 'delete-location-modal',
    template: _.template(modalDeleteLocationTemplate),
    title: 'Delete Location',
    okText: 'Delete',
    inputMatch: true,
    initialize: function() {
      ModalDeleteLocationView.__super__.initialize.call(this);
      this.inputMatchText = this.model.get('name');
    },
    body: function() {
      return this.template();
    },
    onOk: function() {
      this.setLoading('Deleting location...');
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

  return ModalDeleteLocationView;
});
