define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var OrgModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'name': null,
      'expiration': null,
      'user_count': null
    },
    ttl: function() {
      var expiration = this.get('expiration');
      if (!expiration) {
        return 0;
      }
      var notAfterDate = new Date(expiration);
      var currentDate = new Date();
      var warningDate = new Date();
      warningDate.setFullYear(warningDate.getFullYear() + 2);

      var timeDiff = notAfterDate - currentDate;
      var daysRemaining = Math.floor(timeDiff / (1000 * 60 * 60 * 24));

      if (daysRemaining < 0) {
          return -1;
      }

      if (notAfterDate > warningDate) {
          return 0;
      }

      return daysRemaining;
    },
    url: function() {
      var url = '/organization';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return OrgModel;
});
