define([
  'jquery',
  'underscore',
  'backbone',
  'models/password',
  'views/modal',
  'text!templates/modalChangePassword.html'
], function($, _, Backbone, PasswordModel, ModalView,
    modalChangePasswordTemplate) {
  'use strict';
  var ModalChangePasswordView = ModalView.extend({
    className: 'change-password-modal',
    template: _.template(modalChangePasswordTemplate),
    title: 'Change Password',
    okText: 'Change',
    initialize: function() {
      this.model = new PasswordModel();
      ModalChangePasswordView.__super__.initialize.call(this);
    },
    body: function() {
      return this.template();
    },
    onOk: function() {
      if (!this.$('.pass').val()) {
        this.setAlert('danger', 'Password can not be empty.', '.form-group');
        return;
      }
      if (this.$('.pass').val() !== this.$('.verify-pass').val()) {
        this.setAlert('danger', 'Passwords do not match.', '.form-group');
        return;
      }
      this.setLoading('Changing password...');
      this.model.save({
        password: this.$('.pass').val()
      }, {
        success: function() {
          this.close(true);
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to change password, server error occurred.');
        }.bind(this)
      });
    }
  });

  return ModalChangePasswordView;
});
