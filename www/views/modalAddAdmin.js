define([
  'jquery',
  'underscore',
  'backbone',
  'models/admin',
  'views/modal',
  'text!templates/modalAddAdmin.html'
], function($, _, Backbone, AdminModel, ModalView, modalAddAdminTemplate) {
  'use strict';
  var ModalAddAdminView = ModalView.extend({
    className: 'modify-admin-modal',
    template: _.template(modalAddAdminTemplate),
    title: 'Add Administrator',
    okText: 'Add',
    enterOk: false,
    events: function() {
      return _.extend({
        'click .super-user-toggle': 'onSuperSelect',
        'click .otp-auth-toggle': 'onOtpAuthSelect',
        'click .auth-api-toggle': 'onAuthSelect',
        'click .auth-token input, .auth-secret input': 'onClickInput'
      }, ModalAddAdminView.__super__.events);
    },
    body: function() {
      return this.template();
    },
    update: function() {
      this.$('.auth-token input').val(this.model.get('auth_token'));
      this.$('.auth-secret input').val(this.model.get('auth_secret'));
    },
    getSuperSelect: function() {
      return this.$('.super-user-toggle .selector').hasClass('selected');
    },
    setSuperSelect: function(state) {
      if (state) {
        this.$('.super-user-toggle .selector').addClass('selected');
        this.$('.super-user-toggle .selector-inner').show();
      } else {
        this.$('.super-user-toggle .selector').removeClass('selected');
        this.$('.super-user-toggle .selector-inner').hide();
      }
    },
    onSuperSelect: function() {
      this.setSuperSelect(!this.getSuperSelect());
    },
    getOtpAuthSelect: function() {
      return this.$('.otp-auth-toggle .selector').hasClass('selected');
    },
    setOtpAuthSelect: function(state) {
      if (state) {
        this.$('.otp-auth-toggle .selector').addClass('selected');
        this.$('.otp-auth-toggle .selector-inner').show();
      } else {
        this.$('.otp-auth-toggle .selector').removeClass('selected');
        this.$('.otp-auth-toggle .selector-inner').hide();
      }
    },
    onOtpAuthSelect: function() {
      this.setOtpAuthSelect(!this.getOtpAuthSelect());
    },
    getAuthSelect: function() {
      return this.$('.auth-api-toggle .selector').hasClass('selected');
    },
    setAuthSelect: function(state) {
      if (state) {
        this.$('.auth-api-toggle .selector').addClass('selected');
        this.$('.auth-api-toggle .selector-inner').show();
        this.$('.auth-token-form').slideDown(window.slideTime);
      } else {
        this.$('.auth-api-toggle .selector').removeClass('selected');
        this.$('.auth-api-toggle .selector-inner').hide();
        this.$('.auth-token-form').slideUp(window.slideTime);
      }
    },
    onAuthSelect: function() {
      this.setAuthSelect(!this.getAuthSelect());
    },
    onClickInput: function(evt) {
      this.$(evt.target).select();
    },
    onOk: function() {
      var username = this.$('.username input').val();
      var password = this.$('.password input').val();
      var yubikeyId = this.$('.yubikey-id input').val();
      var superUser = this.getSuperSelect();
      var otpAuth = this.getOtpAuthSelect();
      var authApi = this.getAuthSelect();

      if (!username) {
        this.setAlert('danger', 'Username can not be empty.', '.username');
        return;
      }

      if (!password) {
        this.setAlert('danger', 'Password can not be empty.', '.username');
        return;
      }

      var data = {
        username: username,
        password: password,
        yubikey_id: yubikeyId,
        super_user: superUser,
        otp_auth: otpAuth,
        auth_api: authApi,
        token: null,
        secret: null
      };

      this.setLoading('Adding administrator...');
      var adminModel = new AdminModel();
      adminModel.save(data, {
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

  return ModalAddAdminView;
});
