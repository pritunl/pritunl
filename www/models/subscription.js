define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var SubscriptionModel = Backbone.Model.extend({
    defaults: {
      'license': null,
      'card': null,
      'email': null,
      'active': null,
      'status': null,
      'amount': null,
      'period_end': null,
      'cancel_at_period_end': null
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
        loadMsg = 'Updating payment information, please wait...';
        completeMsg = 'Payment information successfully updated, you will '+
          'not be charged until the end of the current subscription period.';
        return ['Active', 'success-text', 'checkout_update',
          loadMsg, completeMsg];
      }
    }
  });

  return SubscriptionModel;
});
