define([
  'jquery',
  'underscore',
  'backbone',
  'qrcode',
  'models/subscription',
  'views/modal',
  'views/alert',
  'text!templates/modalSubscribe.html'
], function($, _, Backbone, QRCode, SubscriptionModel, ModalView, AlertView,
    modalSubscribeTemplate) {
  'use strict';
  var ModalSubscribeView = ModalView.extend({
    className: 'subscribe-modal',
    template: _.template(modalSubscribeTemplate),
    title: 'Upgrade Subscription',
    cancelText: null,
    okText: 'Close',
    enterOk: false,
    safeClose: true,
    initialize: function() {
      ModalSubscribeView.__super__.initialize.call(this);
    },
    events: function() {
      return _.extend({
        'click .subscribe-premium': 'onPremium',
        'click .subscribe-enterprise': 'onEnterprise',
        'click .subscribe-enterprise-plus': 'onEnterprisePlus',
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
      this.$('.subscribe-premium').attr('disabled', 'disabled');
      this.$('.subscribe-enterprise').attr('disabled', 'disabled');
      this.$('.subscribe-enterprise-plus').attr('disabled', 'disabled');
      this.$('.subscribe-activate').attr('disabled', 'disabled');
    },
    unlock: function(noCheckout) {
      this.lockClose = false;
      this.$('.ok').removeAttr('disabled');
      if (!noCheckout) {
        this.$('.subscribe-premium').removeAttr('disabled');
        this.$('.subscribe-enterprise').removeAttr('disabled');
        this.$('.subscribe-enterprise-plus').removeAttr('disabled');
      }
      this.$('.subscribe-activate').removeAttr('disabled');
    },
    setupCheckout: function() {
      this.checkout = undefined;
      $.ajax({
          type: 'GET',
          url: 'https://app.pritunl.com/checkout',
          success: function(options) {
            this.plans = options.plans;
            delete options.plans;

            if (this.plans.premium && this.plans.premium.amount) {
              this.$('.subscribe-premium').text('Get Premium $' +
                (this.plans.premium.amount / 100) + '/month');
            }
            if (this.plans.enterprise && this.plans.enterprise.amount) {
              this.$('.subscribe-enterprise').text('Get Enterprise $' +
                (this.plans.enterprise.amount / 100) + '/month');
            }
            if (this.plans.enterprise_plus &&
                this.plans.enterprise_plus.amount) {
              this.$('.subscribe-enterprise-plus').text('Get Enterprise+ $' +
                (this.plans.enterprise_plus.amount / 100) + '/month');
            }
            this.configCheckout(options);
          }.bind(this),
          error: function() {
            this.setAlert('danger', 'Failed to load checkout data, ' +
              'please try again later.');
            this.checkout = false;
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
                  'plan': this.plan,
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
                    this.setAlert('danger', 'Server error occurred, ' +
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
          this.checkout = false;
        }.bind(this)
      });
    },
    openCheckout: function(plan) {
      if (this.checkout === undefined) {
        setTimeout(function() {
          this.openCheckout(plan);
        }.bind(this), 10);
      }
      else if (this.checkout === false) {
        this.unlock();
      }
      else {
        this.checkout.open(this.plans[plan]);
      }
    },
    _onCheckout: function(plan) {
      this.lock();
      this.clearAlert();
      this.plan = plan;
      if (this.checkout === false) {
        this.setupCheckout();
      }
      this.openCheckout(plan);
    },
    onPremium: function() {
      this._onCheckout('premium');
    },
    onEnterprise: function() {
      this._onCheckout('enterprise');
    },
    onEnterprisePlus: function() {
      this._onCheckout('enterprise_plus');
    },
    onActivate: function() {
      this.activateActive = true;
      this.$('.subscribe-info').slideUp(window.slideTime);
      this.$('.subscribe-activate-form').slideDown(window.slideTime);
      this.$('.subscribe-premium').hide();
      this.$('.subscribe-enterprise').hide();
      this.$('.subscribe-enterprise-plus').hide();
      this.$('.subscribe-cancel').show();
      this.$('.subscribe-activate').hide();
      this.$('.subscribe-submit').show();
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
            this.setAlert('danger', 'Server error occurred, ' +
              'please try again later.');
          }
          this.$('.subscribe-submit').removeAttr('disabled');
        }.bind(this)
      });
    },
    onCancel: function() {
      this.$('.subscribe-activate-form').slideUp(window.slideTime);
      this.$('.subscribe-info').slideDown(window.slideTime);
      this.$('.subscribe-cancel').hide();
      this.$('.subscribe-premium').show();
      this.$('.subscribe-enterprise').show();
      this.$('.subscribe-enterprise-plus').show();
      this.$('.subscribe-submit').hide();
      this.$('.subscribe-activate').show();
      this.activateActive = false;
    }
  });

  return ModalSubscribeView;
});
