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
        'click .enterprise-remove': 'onRemoveLicense'
      }, ModalEnterpriseView.__super__.events);
    },
    body: function() {
      return this.template(this.model.toJSON());
    },
    postRender: function() {
      this.update();
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
        this.$('.renew .enterprise-label').text('Plan Ends:');
      }
      else {
        this.$('.renew .enterprise-label').text('Renew:');
      }

      if (this.model.get('url_key')) {
        this.$('.key .enterprise-label').text(this.model.get('url_key'));
        this.$('.key').show();
      }
      else {
        this.$('.key').hide();
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
        this.$('.enterprise-billing').attr(this.model.get('portal_url'));
      }

      if (this.model.get('premium_buy_url')) {
        this.$('.enterprise-premium-buy').attr(
          this.model.get('premium_buy_url'));
        this.$('.enterprise-premium-buy').show();
      } else {
        this.$('.enterprise-premium-buy').hide();
      }

      if (this.model.get('enterprise_buy_url')) {
        this.$('.enterprise-enterprise-buy').attr(
          this.model.get('enterprise_buy_url'));
        this.$('.enterprise-enterprise-buy').show();
      } else {
        this.$('.enterprise-enterprise-buy').hide();
      }

      if (this.model.get('quantity') === 1000) {
        this.$('.quantity').hide();
        this.$('.quantity').hide();
        this.$('.renew').hide();
        this.$('.enterprise-support-link').hide();
        this.$('.enterprise-plus-plan').text('Dedicated');
      }
    },
    onRemoveLicense: function() {
      if (this.$('.enterprise-remove').text() === 'Remove License') {
        this.$('.enterprise-remove').text('Are you sure?');
        setTimeout(function() {
          this.$('.enterprise-remove').text('Remove License');
        }, 5000);
        return;
      }
      this.$('.enterprise-remove').attr('disabled', 'disabled');
      this.$('.enterprise-remove').text('Remove License');
      this.model.destroy({
        success: function() {
          this.$('.enterprise-remove').removeAttr('disabled');
          this.close(true);
        }.bind(this),
        error: function(model, response) {
          this.$('.enterprise-remove').removeAttr('disabled');
          if (response.responseJSON) {
            this.setAlert('danger', response.responseJSON.error_msg);
          }
          else {
            this.setAlert('danger', this.errorMsg);
          }
        }.bind(this)
      });
    },
  });

  return ModalEnterpriseView;
});
