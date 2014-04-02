define([
  'jquery',
  'underscore',
  'backbone',
  'models/auth',
  'views/alert',
  'views/login',
  'views/modalChangePassword',
  'text!templates/header.html'
], function($, _, Backbone, AuthModel, AlertView, LoginView,
    ModalChangePasswordView, headerTemplate) {
  'use strict';
  var HeaderView = Backbone.View.extend({
    tagName: 'header',
    template: _.template(headerTemplate),
    events: {
      'click .enterprise-upgrade a': 'onEnterpriseUpgrade',
      'click .change-password a': 'changePassword'
    },
    render: function() {
      this.$el.html(this.template());
      return this;
    },
    onEnterpriseUpgrade: function() {
      if (this.onEnterpriseUpgradeLock) {
        return;
      }
      this.onEnterpriseUpgradeLock = true;
      $.getCachedScript('https://checkout.stripe.com/checkout.js', {
        success: function() {
          var checkout = window.StripeCheckout.configure({
            key: 'pk_test_cex9CxHTANzcSdOdeoqhgMy9',
            image: 'https://s3.amazonaws.com/pritunl/logo_stripe.svg',
            name: 'Pritunl Enterprise',
            description: 'Enterprise Plan ($2.50/month)',
            amount: 250,
            panelLabel: 'Subscribe',
            allowRememberMe: false,
            opened: function() {
              this.onEnterpriseUpgradeLock = false;
            }.bind(this),
            token: function(token, args) {
              console.log(token, args);
            }
          });
          checkout.open();
        }.bind(this),
        error: function() {
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to load upgrade checkout, try again later.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
          this.onEnterpriseUpgradeLock = false;
        }.bind(this)
      });
    },
    changePassword: function() {
      var loginView = new LoginView({
        showChangePassword: true
      });
      if (loginView.active) {
        $('body').append(loginView.render().el);
        this.addView(loginView);
      }
    }
  });

  return HeaderView;
});
