define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalDeleteServer.html'
], function($, _, Backbone, ModalView, AlertView, modalDeleteServerTemplate) {
  'use strict';
  var ModalDeleteServerView = ModalView.extend({
    className: 'delete-server-modal',
    template: _.template(modalDeleteServerTemplate),
    title: 'Delete Server',
    okText: 'Delete',
    inputMatch: true,
    initialize: function() {
      this.constructor.__super__.initialize.call(this);
      var alertView = new AlertView({
        type: 'danger',
        message: 'Deleting the server will delete all the users in it.',
        animate: false
      });
      this.addView(alertView);
      this.$('.modal-body').prepend(alertView.render().el);
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
