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
    safeClose: true,
    events: function() {
      return _.extend({
        'click .subscribe-checkout': 'onCheckout'
      }, ModalSubscribeView.__super__.events);
    },
    body: function() {
      return this.template();
    },
    lock: function() {
      this.lockClose = true;
      this.$('.ok').attr('disabled', 'disabled');
      this.$('.subscribe-checkout').attr('disabled', 'disabled');
      this.$('.subscribe-activate').attr('disabled', 'disabled');
    },
    unlock: function(noCheckout) {
      this.lockClose = false;
      this.$('.ok').removeAttr('disabled');
      if (!noCheckout) {
        this.$('.subscribe-checkout').removeAttr('disabled');
      }
      this.$('.subscribe-activate').removeAttr('disabled');
    },
    onCheckout: function() {
      this.lock();
      $.getCachedScript('https://checkout.stripe.com/checkout.js', {
        success: function() {
          var ordered = false;
          var checkout = window.StripeCheckout.configure({
            key: 'pk_test_cex9CxHTANzcSdOdeoqhgMy9',
            image: 'https://s3.amazonaws.com/pritunl/logo_stripe.png',
            name: 'Pritunl Enterprise',
            description: 'Enterprise Plan ($2.50/month)',
            amount: 250,
            panelLabel: 'Subscribe',
            allowRememberMe: false,
            closed: function() {
              setTimeout(function() {
                if (!ordered) {
                  this.unlock();
                }
              }.bind(this), 250);
            }.bind(this),
            token: function(token) {
              ordered = true;
              this.lock();
              this.setLoading('Order processing, please wait...', true, 0);
              $.ajax({
                type: 'POST',
                url: 'https://app.pritunl.com/subscription',
                contentType: 'application/json',
                dataType: 'json',
                data: JSON.stringify({
                  'card': token.id,
                  'email': token.email,
                }),
                success: function(response) {
                  this.setAlert('success', response.msg);
                  this.clearLoading();
                  this.unlock(true);
                }.bind(this),
                error: function(response) {
                  if (response.responseJSON) {
                    this.setAlert('danger', response.responseJSON.error_msg);
                  }
                  else {
                    this.setAlert('danger', 'Unknown error occured, ' +
                      'please try again later.');
                  }
                  this.clearLoading();
                  this.unlock();
                }.bind(this)
              });
            }.bind(this)
          });
          checkout.open();
        }.bind(this),
        error: function() {
          this.setAlert('danger', 'Failed to load upgrade checkout, ' +
            'please try again later.');
          this.unlock();
        }.bind(this)
      });
    }
  });

  return ModalSubscribeView;
});
