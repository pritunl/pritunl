define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalDeleteOrg.html'
], function($, _, Backbone, ModalView, AlertView, modalDeleteOrgTemplate) {
  'use strict';
  var ModalDeleteServerView = ModalView.extend({
    className: 'delete-server-modal',
    template: _.template(modalDeleteOrgTemplate),
    title: 'Delete Server',
    okText: 'Delete',
    initialize: function() {
      ModalDeleteServerView.__super__.initialize.call(this);
      var alertView = new AlertView({
        type: 'danger',
        message: 'Deleting the server will delete all the users in it.',
        animate: false
      });
      this.addView(alertView);
      this.$('form').prepend(alertView.render().el);
    },
    body: function() {
      return this.template();
    },
    onOk: function() {
      if (this.locked) {
        return;
      }
      if (this.$('input').val() !== this.model.get('name')) {
        this.setAlert('info', 'Name entered doesn\'t match the name ' +
          'of the server being deleted.', '.form-group');
        return;
      }
      this.locked = true;
      this.setLoading('Deleting server...');
      this.model.destroy({
        success: function() {
          this.close(true);
        }.bind(this),
        error: function() {
          this.setAlert('danger',
            'Failed to delete server, server error occurred.');
          this.locked = false;
        }.bind(this)
      });
    }
  });

  return ModalDeleteServerView;
});
