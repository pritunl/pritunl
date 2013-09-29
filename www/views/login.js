define([
  'jquery',
  'underscore',
  'backbone',
  'models/auth',
  'views/loginBackdrop',
  'text!templates/login.html'
], function($, _, Backbone, AuthModel, LoginBackdropView, loginTemplate) {
  'use strict';
  var LoginView = Backbone.View.extend({
    className: 'login',
    template: _.template(loginTemplate),
    events: {
      'click .login-button': 'onLogin',
      'keypress input': 'onKeypress'
    },
    initialize: function(options) {
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
      return this;
    },
    onKeypress: function(evt) {
      if (evt.keyCode === 13) {
        this.onLogin();
      }
    },
    onLogin: function() {
      var authModel = new AuthModel();
      authModel.save({
        username: this.$('.form-control[type="text"]').val(),
        password: this.$('.form-control[type="password"]').val()
      }, {
        success: function() {
          this.callback();
        }.bind(this)
      });
    }
  });

  return LoginView;
});
