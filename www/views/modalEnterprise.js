define([
  'jquery',
  'underscore',
  'backbone',
  'qrcode',
  'models/subscription',
  'views/modal',
  'text!templates/modalEnterprise.html'
], function($, _, Backbone, QRCode, SubscriptionModel, ModalView,
    modalEnterpriseTemplate) {
  'use strict';
  var ModalSubscribeView = ModalView.extend({
    className: 'enterprise-modal',
    template: _.template(modalEnterpriseTemplate),
    title: 'Enterprise Information',
    cancelText: null,
    okText: 'Close',
    safeClose: true,
    events: function() {
      return _.extend({
        'click .enterprise-update': 'onCheckout',
        'click .enterprise-remove': 'onRemoveLicense',
        'click .enterprise-cancel': 'onCancelLicense'
      }, ModalSubscribeView.__super__.events);
    },
    body: function() {
      return this.template(this.model.toJSON());
    },
    postRender: function() {
      this.update();
      // Precache checkout and uservoice with delay to prevent animation lag
      setTimeout((this.setupUserVoice).bind(this), 200);
      setTimeout((this.setupCheckout).bind(this), 200);
    },
    update: function() {
      var statusText = this.model.getTextStatus();
      var colors = ['default-text', 'error-text',
        'warning-text', 'success-text'];
      colors.splice(colors.indexOf(statusText[1]), 1);
      this.$('.enterprise-item.status').text(statusText[0]);
      this.$('.enterprise-item.status').removeClass(colors.join(' '));
      this.$('.enterprise-item.status').addClass(statusText[1]);
      this.$('.enterprise-item.amount').text('$' +
        (this.model.get('amount') / 100).toFixed(2));
      this.$('.enterprise-item.renew').text(
        window.formatTime(this.model.get('period_end'), 'date'));
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
    setupUserVoice: function() {
      $.getCachedScript('//widget.uservoice.com/Vp7EFBMcYhZHI91VAtHeyg.js', {
        success: function() {
          window.UserVoice.push(['set', {
            contact_title: 'Contact Support',
            accent_color: '#448dd6',
            screenshot_enabled: false,
            smartvote_enabled: false,
            post_idea_enabled: false
          }]);
          window.UserVoice.push(['identify', {
            plan: 'enterprise',
          }]);
          window.UserVoice.push(['addTrigger', '#trigger-uservoice',
            {mode: 'contact'}]);
          window.UserVoice.push(['autoprompt', {}]);
        }.bind(this),
        error: function() {
          this.$('.enterprise-support').attr('disabled', 'disabled');
        }.bind(this)
      });
    },
    setupCheckout: function() {
      this.checkout = undefined;
      $.ajax({
          type: 'GET',
          url: 'https://app.pritunl.com/checkout_update',
          success: function(options) {
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
              }.bind(this), 100);
            }.bind(this),
            token: function(token) {
              ordered = true;
              this.lock();
              this.setLoading('Updating payment information, please wait...',
                true, 0);
              this.model.save({
                card: token.id,
                email: token.email
              }, {
                success: function() {
                  this.setAlert('success', 'Payment information ' +
                    'updated successfully.');
                  this.clearLoading();
                  this.unlock(true);
                  this.update();
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
    onRemoveLicense: function() {
      this.model.destroy({
        success: function() {
          this.close(true);
        }.bind(this),
        error: function() {
          this.setAlert('danger', 'Unknown server error occured, ' +
            'please try again later.');
        }.bind(this)
      })
    },
    onCancelLicense: function() {
      this.model.save({
        cancel: true
      }, {
        success: function() {
          this.setAlert('info', 'Subscription successfully canceled, ' +
            'subscription will stay active until the end of the ' +
            'current period.');
          this.update();
        }.bind(this),
        error: function() {
          this.setAlert('danger', 'Unknown server error occured, ' +
            'please try again later.');
        }.bind(this)
      })
    }
  });

  return ModalSubscribeView;
});
