define([
  'jquery',
  'underscore',
  'backbone',
  'models/auth',
  'models/authSession',
  'views/alert',
  'views/loginBackdrop',
  'views/modalSettings',
  'text!templates/login.html'
], function($, _, Backbone, AuthModel, AuthSessionModel, AlertView,
    LoginBackdropView, ModalSettingsView, loginTemplate) {
  'use strict';
  var LoginView = Backbone.View.extend({
    className: 'login',
    template: _.template(loginTemplate),
    events: {
      'click .login-button': 'login',
      'keypress input': 'onKeypress'
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
      this.showSettings = options.showSettings;
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
      if (window.demo) {
        this.$('.username, .password').val('demo');
      }
      return this;
    },
    onKeypress: function(evt) {
      if (evt.keyCode === 13) {
        this.login();
      }
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
    openSettings: function(username, password, initial) {
      var model = new AuthModel({
        username: username,
        password: password
      });
      model.fetch({
        success: function() {
          var modal = new ModalSettingsView({
            initial: initial,
            model: model
          });
          this.listenToOnce(modal, 'applied', function() {
            var alertView = new AlertView({
              type: 'warning',
              message: 'Successfully changed password.',
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
            message: 'Failed to load auth authentication, ' +
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
              var initial;
              this.destroy();
              if (model.get('default_password') || this.showSettings) {
                if (!this.showSettings) {
                  initial = true;
                }
                this.openSettings(username, password, initial);
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
    }
  });

  return LoginView;
});
