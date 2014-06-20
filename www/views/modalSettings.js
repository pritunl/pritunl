define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalSettings.html'
], function($, _, Backbone, ModalView, modalSettingsTemplate) {
  'use strict';
  var ModalSettingsView = ModalView.extend({
    className: 'change-password-modal',
    template: _.template(modalSettingsTemplate),
    title: 'Settings',
    okText: 'Save',
    events: function() {
      return _.extend({
        'click .generate-new-api-key': 'onGenerateNewKey',
        'click .right input': 'onClickInput'
      }, ModalSettingsView.__super__.events);
    },
    initialize: function(options) {
      this.initial = options.initial;
      if (this.initial) {
        this.title = 'Initial Setup';
        this.okText = 'Save';
        this.cancelText = 'Setup Later';
      }
      ModalSettingsView.__super__.initialize.call(this);
    },
    body: function() {
      return this.template(_.extend({
        initial: this.initial
      }, this.model.toJSON()));
    },
    update: function() {
      this.$('.api-token input').val(this.model.get('token'));
      this.$('.api-secret input').val(this.model.get('secret'));
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
    onGenerateNewKey: function() {
      this.setLoading('Generating new api key...');
      this.model.save({
        token: null,
        secret: null
      }, {
        success: function() {
          this.clearLoading();
          this.setAlert('warning', 'Successfully generated a new api key.');
          this.update();
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to change password, server error occurred.');
        }.bind(this)
      });
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

  return ModalSettingsView;
});
