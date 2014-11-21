define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalSettings.html'
], function($, _, Backbone, ModalView, modalSettingsTemplate) {
  'use strict';
  var ModalSettingsView = ModalView.extend({
    className: 'settings-modal',
    template: _.template(modalSettingsTemplate),
    title: 'Settings',
    okText: 'Save',
    events: function() {
      return _.extend({
        'change .theme select': 'onThemeChange',
        'click .generate-new-api-key': 'onGenerateNewKey',
        'click .right input': 'onClickInput'
      }, ModalSettingsView.__super__.events);
    },
    initialize: function(options) {
      this.initial = options.initial;
      if (this.initial) {
        this.title = 'Initial Setup';
        this.cancelText = 'Setup Later';
      }
      ModalSettingsView.__super__.initialize.call(this);
    },
    body: function() {
      return this.template(this.model.toJSON());
    },
    update: function() {
      this.$('.api-token input').val(this.model.get('token'));
      this.$('.api-secret input').val(this.model.get('secret'));
    },
    onThemeChange: function() {
      if (this.$('.theme select').val() === 'dark') {
        $('body').addClass('dark');
      }
      else {
        $('body').removeClass('dark');
      }
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
      this.model.clear();
      this.model.save({
        token: true,
        secret: true
      }, {
        success: function() {
          this.clearLoading();
          this.setAlert('warning', 'Successfully generated a new api key.');
          this.update();
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to generated a new api key, server error occurred.');
        }.bind(this)
      });
    },
    onOk: function() {
      var username = this.$('.username input').val();
      var password = this.$('.pass input').val();
      var publicAddress = this.$('.public-address input').val();
      var theme = this.$('.theme select').val();
      var verifyPassword = this.$('.verify-pass input').val();
      var emailFromAddr = this.$('.email-from-addr input').val();
      var emailApiKey = this.$('.email-api-key input').val();
      var emailReg = /^\w+([-+.']\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/;
      var modelAttr = {
        username: username,
        email_from: emailFromAddr,
        email_api_key: emailApiKey,
        public_address: publicAddress,
        theme: theme
      };

      if (!username) {
        this.setAlert('danger', 'Username can not be empty.', '.username');
        return;
      }
      if (password) {
        if (password !== verifyPassword) {
          this.setAlert('danger', 'Passwords do not match.', '.verify-pass');
          return;
        }
        modelAttr.password = password;
      }
      if (emailFromAddr && !emailReg.test(emailFromAddr)) {
        this.setAlert('danger', 'From email is not valid.',
          '.email-from-addr');
        return;
      }
      this.setLoading('Saving settings...');
      this.model.clear();
      this.model.save(modelAttr, {
        success: function() {
          this.close(true);
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to save settings, server error occurred.');
        }.bind(this)
      });
    },
    onClickInput: function(evt) {
      this.$(evt.target).select();
    },
    onRemove: function() {
      ModalSettingsView.__super__.onRemove.call(this);
      if (!this.triggerApplied) {
        if (window.theme === 'dark') {
          $('body').addClass('dark');
        }
        else {
          $('body').removeClass('dark');
        }
      }
    }
  });

  return ModalSettingsView;
});
