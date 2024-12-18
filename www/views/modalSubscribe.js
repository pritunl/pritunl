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
        'click .subscribe-activate': 'onActivate',
        'click .subscribe-submit': 'onSubmit',
        'click .subscribe-cancel': 'onCancel'
      }, ModalSubscribeView.__super__.events);
    },
    body: function() {
      return this.template();
    },
    postRender: function() {
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
