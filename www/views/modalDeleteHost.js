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
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to delete host, server error occurred.');
        }.bind(this)
      });
    }
  });

  return ModalDeleteHostView;
});
