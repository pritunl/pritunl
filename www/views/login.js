define([
  'jquery',
  'underscore',
  'backbone',
  'models/settings',
  'models/authSession',
  'views/alert',
  'views/loginBackdrop',
  'views/modalSettings',
  'text!templates/login.html'
], function($, _, Backbone, SettingsModel, AuthSessionModel, AlertView,
    LoginBackdropView, ModalSettingsView, loginTemplate) {
  'use strict';
  var LoginView = Backbone.View.extend({
    className: 'login',
    template: _.template(loginTemplate),
    events: {
      'submit .login-form': 'login'
    },
    initialize: function(options) {
      if (window.loginViewLock) {
        this.active = false;
        this.destroy();
        return;
      }
      window.loginViewLock = true;
      this.active = true;
      this.alert = options.alert;
      this.callback = options.callback;
      this.backdrop = new LoginBackdropView();
      this.addView(this.backdrop);
    },
    deinitialize: function() {
      if (this.active) {
        $('header').removeClass('blur');
        $('#app').removeClass('blur');
      }
    },
    render: function() {
      this.$el.html(this.template());
      $('header').addClass('blur');
      $('#app').addClass('blur');
      $('body').append(this.backdrop.render().el);
      if (this.alert) {
        this.setAlert(this.alert);
      }
      if (window.sso === 'google' || window.sso === 'google_duo') {
        this.$('form').addClass('sso-google');
      } else if (window.sso === 'duo') {
        this.$('form').addClass('sso-duo');
      }
      if (window.demo) {
        this.$('.username, .password').val('demo');
      }
      return this;
    },
    setAlert: function(message) {
      if (this.alertView) {
        if (this.alertView.message !== message) {
          this.alertView.close(function() {
            this.setAlert(message);
          }.bind(this));
          this.alertView = null;
        }
        else {
          this.alertView.flash();
        }
        return;
      }

      this.alertView = new AlertView({
        type: 'danger',
        message: message,
        force: true
      });
      this.$('.login-form').prepend(this.alertView.render().el);
      this.addView(this.alertView);
      this.$('input').addClass('has-warning');
    },
    openSettings: function() {
      var model = new SettingsModel();
      model.fetch({
        success: function() {
          var modal = new ModalSettingsView({
            initial: true,
            model: model
          });
          this.listenToOnce(modal, 'applied', function() {
            var alertView = new AlertView({
              type: 'success',
              message: 'Successfully saved settings.',
              dismissable: true
            });
            $('.alerts-container').append(alertView.render().el);
            this.addView(alertView);
          }.bind(this));
          this.addView(modal);
        }.bind(this),
        error: function() {
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to load authentication data, ' +
              'server error occurred.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
        }.bind(this)
      });
    },
    login: function() {
      this.$('.login-button').attr('disabled', 'disabled');
      var username = this.$('.username').val();
      var password = this.$('.password').val();

      var authSessionModel = new AuthSessionModel();
      authSessionModel.save({
        username: username,
        password: password
      }, {
        success: function(model) {
          if (this.callback) {
            this.callback();
          }
          this.backdrop.$el.fadeOut(400);
          this.$('.login-box').animate({
            top: '-50%'
          }, {
            duration: 400,
            complete: function() {
              this.destroy();
              if (model.get('default')) {
                this.openSettings();
              }
              window.loginViewLock = false;
            }.bind(this)
          });
          $('header').removeClass('blur');
          $('#app').removeClass('blur');
        }.bind(this),
        error: function(model, response) {
          this.$('.login-button').removeAttr('disabled');
          if (response.responseJSON && response.responseJSON.error_msg) {
            this.setAlert(response.responseJSON.error_msg);
          }
          else {
            this.setAlert('Server error occurred.');
          }
        }.bind(this)
      });

      return false;
    }
  });

  return LoginView;
});
