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
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to delete server, server error occurred.');
        }.bind(this)
      });
    }
  });

  return ModalDeleteServerView;
});
