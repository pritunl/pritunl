define([
  'jquery',
  'underscore',
  'backbone',
  'qrcode',
  'views/modal',
  'text!templates/modalSubscribe.html'
], function($, _, Backbone, QRCode, ModalView, modalSubscribeTemplate) {
  'use strict';
  var ModalSubscribeView = ModalView.extend({
    className: 'subscribe-modal',
    template: _.template(modalSubscribeTemplate),
    title: 'Enterprise Upgrade',
    cancelText: null,
    okText: 'Close',
    events: function() {
      return _.extend({
        'click .subscribe-checkout': 'onCheckout'
      }, ModalSubscribeView.__super__.events);
    },
    body: function() {
      return this.template();
    },
    onCheckout: function(evt) {
      this.$('.subscribe-checkout').attr('disabled', 'disabled');
      $.getCachedScript('https://checkout.stripe.com/checkout.js', {
        success: function() {
          var checkout = window.StripeCheckout.configure({
            key: 'pk_test_cex9CxHTANzcSdOdeoqhgMy9',
            image: 'https://s3.amazonaws.com/pritunl/logo_stripe.png',
            name: 'Pritunl Enterprise',
            description: 'Enterprise Plan ($2.50/month)',
            amount: 250,
            panelLabel: 'Subscribe',
            allowRememberMe: false,
            opened: function() {
              this.$('.subscribe-checkout').removeAttr('disabled');
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
          this.$('.subscribe-checkout').removeAttr('disabled');
        }.bind(this)
      });
    }
  });

  return ModalSubscribeView;
});
