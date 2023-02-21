define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var SubscriptionModel = Backbone.Model.extend({
    defaults: {
      'card': null,
      'email': null,
      'premium_buy_url': null,
      'enterprise_buy_url': null,
      'portal_url': null,
      'url_key': null,
      'active': null,
      'status': null,
      'plan': null,
      'quantity': null,
      'amount': null,
      'period_end': null,
      'trial_end': null,
      'cancel_at_period_end': null,
      'balance': null,
      'version': null,
      'theme': null,
      'super_user': null,
      'sso': null
    },
    isNew: function() {
      var active = this.get('active');
      return active === null || active === undefined;
    },
    url: function() {
      return '/subscription';
    },
    parse: function(response) {
      this.unset('cancel');
      return response;
    },
    getStatusData: function() {
      var loadMsg;
      var completeMsg;
      var status = this.get('status');
      if (status === 'canceled') {
        loadMsg = 'Reactivating subscription, please wait...';
        completeMsg = 'Subscription successfully reactivated.';
        return ['Inactive', 'error-text', 'checkout_reactivate',
          loadMsg, completeMsg];
      }
      else if (this.get('cancel_at_period_end')) {
        loadMsg = 'Reactivating subscription, please wait...';
        completeMsg = 'Subscription successfully reactivated, you will '+
          'not be charged until the end of the current subscription period.';
        return ['Canceled', 'error-text', 'checkout_renew',
          loadMsg, completeMsg];
      }
      else if (status === 'past_due') {
        loadMsg = 'Reactivating subscription, please wait...';
        completeMsg = 'Subscription successfully reactivated.';
        return ['Past Due', 'warning-text', 'checkout_reactivate',
          loadMsg, completeMsg];
      }
      else {
        if (status === 'trialing') {
          status = 'Trial Period';
        }
        else {
          status = 'Active';
        }

        loadMsg = 'Updating payment information, please wait...';
        completeMsg = 'Payment information successfully updated, you will '+
          'not be charged until the end of the current subscription period.';
        return [status, 'success-text', 'checkout_update',
          loadMsg, completeMsg];
      }
    }
  });

  return SubscriptionModel;
});
