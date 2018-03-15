/*jshint -W030 */
define([
  'jquery',
  'underscore',
  'backbone',
  'qrcode',
  'views/modal',
  'text!templates/modalEnterprise.html'
], function($, _, Backbone, QRCode, ModalView, modalEnterpriseTemplate) {
  'use strict';
  var ModalEnterpriseView = ModalView.extend({
    className: 'enterprise-modal',
    template: _.template(modalEnterpriseTemplate),
    title: 'Subscription Information',
    cancelText: null,
    okText: 'Close',
    safeClose: true,
    events: function() {
      return _.extend({
        'click .enterprise-update, .enterprise-reactivate': 'onUpdate',
        'click .enterprise-change': 'onChange',
        'click .enterprise-remove': 'onRemoveLicense',
        'click .enterprise-cancel': 'onCancelLicense'
      }, ModalEnterpriseView.__super__.events);
    },
    body: function() {
      return this.template(this.model.toJSON());
    },
    postRender: function() {
      this.update();

      // Precache checkout and uservoice with delay to prevent animation lag
      setTimeout((this.setupCheckout).bind(this), 200);
    },
    update: function() {
      var statusData = this.model.getStatusData();
      this.checkoutPath = statusData[2];
      this.checkoutLoading = statusData[3];
      this.checkoutCompleted = statusData[4];
      var colors = ['default-text', 'error-text',
        'warning-text', 'success-text'];
      colors.splice(colors.indexOf(statusData[1]), 1);
      this.$('.status .enterprise-item').text(statusData[0]);
      this.$('.status .enterprise-item').removeClass(colors.join(' '));
      this.$('.status .enterprise-item').addClass(statusData[1]);

      if (statusData[0] === 'Inactive' || statusData[0] === 'Canceled') {
        this.$('.enterprise-cancel').hide();
        this.$('.enterprise-reactivate').show();
        this.$('.enterprise-update').attr('disabled', 'disabled');
        this.$('.renew .enterprise-label').text('Plan Ends:');
      }
      else {
        this.$('.enterprise-reactivate').hide();
        this.$('.enterprise-cancel').show();
        this.$('.enterprise-update').removeAttr('disabled');
        this.$('.renew .enterprise-label').text('Renew:');
      }

      if (this.model.get('quantity')) {
        this.$('.quantity .enterprise-item').text(this.model.get('quantity'));
      }

      if (this.model.get('amount')) {
        this.$('.amount .enterprise-item').text('$' +
          (this.model.get('amount') / 100).toFixed(2));
        this.$('.amount').show();
      }
      else {
        this.$('.amount').hide();
      }

      if (this.model.get('period_end') && statusData[0] !== 'Inactive') {
        this.$('.renew .enterprise-item').text(
          window.formatTime(this.model.get('period_end'), 'date'));
        this.$('.renew').show();
      }
      else {
        this.$('.renew').hide();
      }

      if (this.model.get('trial_end')) {
        this.$('.trial-end .enterprise-item').text(
          window.formatTime(this.model.get('trial_end'), 'date'));
      }
      else {
        this.$('.trial-end').hide();
      }

      if (this.model.get('balance') && this.model.get('balance') < 0) {
        this.$('.credit .enterprise-item').text('$' +
          (this.model.get('balance') * -1 / 100).toFixed(2));
        this.$('.credit').show();
      }
      else {
        this.$('.credit').hide();
      }

      if (this.model.get('url_key')) {
        this.$('.enterprise-support-link').attr('href',
          'https://app.pritunl.com/support/' + this.model.get('url_key'));
      }

      if (this.model.get('quantity') === 1000) {
        this.$('.quantity').hide();
        this.$('.quantity').hide();
        this.$('.enterprise-change').hide();
        this.$('.enterprise-cancel').hide();
        this.$('.enterprise-reactivate').hide();
        this.$('.enterprise-update').hide();
        this.$('.renew').hide();
        this.$('.enterprise-support-link').hide();
        this.$('.enterprise-plus-plan').text('Dedicated');
      }
    },
    lock: function() {
      this.lockClose = true;
      this.$('.ok').attr('disabled', 'disabled');
      this.$('.enterprise-support-link').attr('disabled', 'disabled');
      this.$('.enterprise-buttons button').attr('disabled', 'disabled');
    },
    unlock: function() {
      var notSel = '';
      this.lockClose = false;
      this.$('.ok').removeAttr('disabled');
      var statusData = this.model.getStatusData();
      if (statusData[0] === 'Inactive' || statusData[0] === 'Canceled') {
        notSel = ':not(.enterprise-update)';
      }
      this.$('.enterprise-support-link').removeAttr('disabled');
      this.$('.enterprise-buttons button' + notSel).removeAttr('disabled');
    },
    openCheckout: function(optionsPath) {
      $.ajax({
        type: 'GET',
        url: 'https://app.pritunl.com/' + optionsPath,
        success: function(options) {
          var plan;
          var changed = (optionsPath === 'checkout_change');

          if (options.plans) {
            if (options.plans[window.subPlan].plan) {
              plan = options.plans[window.subPlan].plan;
              delete options.plans[window.subPlan].plan;
            }
            _.extend(options, options.plans[window.subPlan]);
            delete options.plans;
          }

          this.configCheckout(options, plan, changed);
        }.bind(this),
        error: function() {
          this.setAlert('danger', 'Failed to load checkout data, ' +
            'please try again later.');
        }.bind(this)
      });
    },
    configCheckout: function(options, plan, changed) {
      $.getCachedScript('https://checkout.stripe.com/checkout.js', {
        success: function() {
          var ordered = false;
          var checkout = window.StripeCheckout.configure(_.extend({
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
              this.setLoading(this.checkoutLoading, true, 100);
              this.model.save({
                card: token.id,
                email: token.email,
                plan: plan
              }, {
                success: function() {
                  if (changed) {
                    this.setAlert('success', 'Subscription plan ' +
                      'successfully changed. The payment or credit for the ' +
                      'current month will be prorated into the payment ' +
                      'for the next month.');
                  }
                  else {
                    this.setAlert('success', this.checkoutCompleted);
                  }

                  this.clearLoading();
                  this.unlock();
                  this.update();
                }.bind(this),
                error: function(model, response) {
                  if (response.responseJSON) {
                    this.setAlert('danger', response.responseJSON.error_msg);
                  }
                  else {
                    this.setAlert('danger', this.errorMsg);
                  }
                  this.clearLoading();
                  this.unlock();
                }.bind(this)
              });
            }.bind(this)
          }, options));
          checkout.open();
        }.bind(this),
        error: function() {
          this.setAlert('danger', 'Failed to load checkout, ' +
            'please try again later.');
        }.bind(this)
      });
    },
    setupCheckout: function() {
      $.getCachedScript('https://checkout.stripe.com/checkout.js');
    },
    _onCheckout: function(optionsPath) {
      this.lock();
      this.clearAlert();
      this.openCheckout(optionsPath);
    },
    onChange: function() {
      this._onCheckout('checkout_change');
    },
    onUpdate: function() {
      this._onCheckout(this.checkoutPath);
    },
    onRemoveLicense: function() {
      if (this.$('.enterprise-remove').text() === 'Remove License') {
        this.$('.enterprise-remove').text('Are you sure?');
        setTimeout(function() {
          this.$('.enterprise-remove').text('Remove License');
        }, 5000);
        return;
      }
      this.lock();
      this.$('.enterprise-remove').text('Remove License');
      this.model.destroy({
        success: function() {
          this.unlock();
          this.close(true);
        }.bind(this),
        error: function(model, response) {
          this.unlock();
          if (response.responseJSON) {
            this.setAlert('danger', response.responseJSON.error_msg);
          }
          else {
            this.setAlert('danger', this.errorMsg);
          }
        }.bind(this)
      });
    },
    onCancelLicense: function() {
      if (this.$('.enterprise-cancel').text() === 'Cancel Subscription') {
        this.$('.enterprise-cancel').text('Are you sure?');
        setTimeout(function() {
          this.$('.enterprise-cancel').text('Cancel Subscription');
        }, 5000);
        return;
      }
      this.lock();
      this.model.save({
        cancel: true
      }, {
        success: function() {
          this.unlock();
          this.setAlert('info', 'Subscription successfully canceled, ' +
            'subscription will stay active until the end of the ' +
            'current period.');
          this.update();
        }.bind(this),
        error: function(model, response) {
          this.unlock();
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

  return ModalEnterpriseView;
});
