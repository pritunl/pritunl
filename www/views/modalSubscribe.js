define([
  'jquery',
  'underscore',
  'backbone',
  'qrcode',
  'models/subscription',
  'views/modal',
  'text!templates/modalSubscribe.html'
], function($, _, Backbone, QRCode, SubscriptionModel, ModalView,
    modalSubscribeTemplate) {
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
        'click .subscribe-checkout': 'onCheckout',
        'click .subscribe-activate': 'onActivate',
        'click .subscribe-submit': 'onSubmit',
        'click .subscribe-cancel': 'onCancel'
      }, ModalSubscribeView.__super__.events);
    },
    body: function() {
      return this.template();
    },
    postRender: function() {
      // Precache checkout delay to prevent lag
      setTimeout((this.setupCheckout).bind(this), 200);
      this.$('li').tooltip();
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
    setupCheckout: function() {
      this.checkout = undefined;
      $.ajax({
          type: 'GET',
          url: 'https://app.pritunl.com/checkout',
          success: function(options) {
            if (options.amount) {
              this.$('.subscribe-checkout').text('Subscribe $' +
                (options.amount / 100).toFixed(2));
            }
            this.configCheckout(options);
          }.bind(this),
          error: function() {
            this.setAlert('danger', 'Failed to load checkout data, ' +
              'please try again later.');
            this.checkout = null;
          }.bind(this)
      });
    },
    configCheckout: function(options) {
      $.getCachedScript('https://checkout.stripe.com/checkout.js', {
        success: function() {
          var ordered = false;
          this.checkout = window.StripeCheckout.configure(_.extend({
            closed: function() {
              setTimeout(function() {
                if (!ordered) {
                  this.unlock();
                }
              }.bind(this), 250);
            }.bind(this),
            token: function(token) {
              if (window.demo) {
                this.unlock(true);
                this.onSubmit();
                return;
              }
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
                  'email': token.email
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
                    this.setAlert('danger', 'Server error occured, ' +
                      'please try again later.');
                  }
                  this.clearLoading();
                  this.unlock();
                }.bind(this)
              });
            }.bind(this)
          }, options));
        }.bind(this),
        error: function() {
          this.setAlert('danger', 'Failed to load upgrade checkout, ' +
            'please try again later.');
          this.checkout = null;
        }.bind(this)
      });
    },
    openCheckout: function() {
      if (this.checkout === undefined) {
        setTimeout((this.openCheckout).bind(this), 10);
      }
      else if (this.checkout === null) {
        this.unlock();
      }
      else {
        this.checkout.open();
      }
    },
    onCheckout: function() {
      this.lock();
      this.clearAlert();
      if (this.checkout === null) {
        this.setupCheckout();
      }
      this.openCheckout();
    },
    onActivate: function() {
      this.activateActive = true;
      this.$('.subscribe-info').slideUp(200);
      this.$('.subscribe-activate-form').slideDown(200);
      this.$('.subscribe-checkout').hide(200);
      this.$('.subscribe-cancel').show(200);
      this.$('.subscribe-activate').hide(200);
      this.$('.subscribe-submit').show(200);
    },
    onSubmit: function() {
      if (!this.$('.subscribe-activate-form textarea').val()) {
        this.setAlert('danger', 'License can not be empty.',
          '.subscribe-activate-form textarea');
        return;
      }
      this.$('.subscribe-submit').attr('disabled', 'disabled');
      var model = new SubscriptionModel();
      model.save({
        'license': this.$('.subscribe-activate-form textarea').val()
      }, {
        success: function() {
          this.close(true);
        }.bind(this),
        error: function(model, response) {
          if (response.responseJSON) {
            this.setAlert('danger', response.responseJSON.error_msg);
          }
          else {
            this.setAlert('danger', 'Server error occured, ' +
              'please try again later.');
          }
          this.$('.subscribe-submit').removeAttr('disabled');
        }.bind(this)
      });
    },
    onCancel: function() {
      this.$('.subscribe-activate-form').slideUp(200);
      this.$('.subscribe-info').slideDown(200);
      this.$('.subscribe-cancel').hide(200);
      this.$('.subscribe-checkout').show(200);
      this.$('.subscribe-submit').hide(200);
      this.$('.subscribe-activate').show(200);
      this.activateActive = false;
    }
  });

  return ModalSubscribeView;
});
