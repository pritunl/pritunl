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
    title: 'Enterprise Information',
    cancelText: null,
    okText: 'Close',
    safeClose: true,
    events: function() {
      return _.extend({
        'click .enterprise-update, .enterprise-reactivate': 'onCheckout',
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
      setTimeout((this.setupUserVoice).bind(this), 200);
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
    },
    lock: function() {
      this.lockClose = true;
      this.$('.ok').attr('disabled', 'disabled');
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
      this.$('.enterprise-buttons button' + notSel).removeAttr('disabled');
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
            type: 'Enterprise'
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
    openCheckout: function(optionsPath) {
      $.ajax({
          type: 'GET',
          url: 'https://app.pritunl.com/' + optionsPath,
          success: function(options) {
            this.configCheckout(options);
          }.bind(this),
          error: function() {
            this.setAlert('danger', 'Failed to load checkout data, ' +
              'please try again later.');
          }.bind(this)
      });
    },
    configCheckout: function(options) {
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
                email: token.email
              }, {
                success: function() {
                  this.setAlert('success', this.checkoutCompleted);
                  this.clearLoading();
                  this.unlock();
                  this.update();
                }.bind(this),
                error: function(model, response) {
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
    onCheckout: function() {
      this.lock();
      this.clearAlert();
      this.openCheckout(this.checkoutPath);
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
        error: function() {
          this.unlock();
          this.setAlert('danger', 'Server error occured, ' +
            'please try again later.');
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
        error: function() {
          this.unlock();
          this.setAlert('danger', 'Server error occured, ' +
            'please try again later.');
        }.bind(this)
      });
    }
  });

  return ModalEnterpriseView;
});
