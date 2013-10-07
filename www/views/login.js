define([
  'jquery',
  'underscore',
  'backbone',
  'models/auth',
  'views/alert',
  'views/loginBackdrop',
  'text!templates/login.html'
], function($, _, Backbone, AuthModel, AlertView, LoginBackdropView,
    loginTemplate) {
  'use strict';
  var LoginView = Backbone.View.extend({
    className: 'login',
    template: _.template(loginTemplate),
    events: {
      'click .login-button': 'login',
      'keypress input': 'onKeypress'
    },
    initialize: function(options) {
      this.alert = options.alert;
      this.callback = options.callback;
      this.backdrop = new LoginBackdropView();
      this.addView(this.backdrop);
    },
    deinitialize: function() {
      $('header').removeClass('blur');
      $('#app').removeClass('blur');
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
        message: message
      });
      this.$('.login-form').prepend(this.alertView.render().el);
      this.addView(this.alertView);
      this.$('input').addClass('has-warning');
    },
    login: function() {
      this.$('.login-button').attr('disabled', 'disabled');

      var authModel = new AuthModel();
      authModel.save({
        username: this.$('.username').val(),
        password: this.$('.password').val()
      }, {
        success: function() {
          this.callback();
          this.backdrop.$el.fadeOut(400);
          this.$el.fadeOut(400, function() {
            this.destroy();
          }.bind(this));
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
