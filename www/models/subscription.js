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
      return this.get('active') == null;
    },
    url: function() {
      return '/subscription';
    },
    getTextStatus: function() {
      var status = this.get('status');
      if (status === 'canceled') {
        return ['Inactive', 'error-text'];
      }
      else if (this.get('cancel_at_period_end')) {
        return ['Canceled', 'error-text'];
      }
      else if (status === 'past_due') {
        return ['Past Due', 'warning-text'];
      }
      else {
        return ['Active', 'success-text'];
      }
    }
  });

  return SubscriptionModel;
});
