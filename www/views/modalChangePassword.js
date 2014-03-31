define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalChangePassword.html'
], function($, _, Backbone, ModalView, modalChangePasswordTemplate) {
  'use strict';
  var ModalChangePasswordView = ModalView.extend({
    className: 'change-password-modal',
    template: _.template(modalChangePasswordTemplate),
    title: 'Change Password',
    okText: 'Change',
    events: function() {
      return _.extend({
        'click .right input': 'onClickInput'
      }, ModalChangePasswordView.__super__.events);
    },
    initialize: function() {
      ModalChangePasswordView.__super__.initialize.call(this);
    },
    body: function() {
      return this.template(this.model.toJSON());
    },
    onInputChange: function() {
      var pass = this.$('.pass input').val();
      if (pass && (
            pass.length < 8 || !pass.match(/[0-9]/) ||
            (
              !pass.match(/[^a-zA-Z0-9]/) &&
              (!pass.match(/[a-z]/) || !pass.match(/[A-Z]/))
            )
          )) {
        this.setAlert('warning', 'Weak password.', '.pass');
      }
      else {
        this.clearAlert();
      }
    },
    onOk: function() {
      var username = this.$('.username input').val();
      var password = this.$('.pass input').val();
      var verifyPassword = this.$('.verify-pass input').val();

      if (!username) {
        this.setAlert('danger', 'Username can not be empty.', '.username');
        return;
      }
      if (!password) {
        this.setAlert('danger', 'Password can not be empty.', '.pass');
        return;
      }
      if (password !== verifyPassword) {
        this.setAlert('danger', 'Passwords do not match.', '.verify-pass');
        return;
      }
      this.setLoading('Changing password...');
      this.model.save({
        username: username,
        password: password
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
    },
    onClickInput: function(evt) {
      this.$(evt.target).select();
    }
  });

  return ModalChangePasswordView;
});
