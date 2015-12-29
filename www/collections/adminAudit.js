define([
  'jquery',
  'underscore',
  'backbone',
  'models/userAudit'
], function($, _, Backbone, UserAuditModel) {
  'use strict';
  var AdminAuditCollection = Backbone.Collection.extend({
    model: UserAuditModel,
    initialize: function(options) {
      this.user = options.user;
    },
    url: function() {
      return '/admin/' + this.user.get('id') + '/audit';
    }
  });

  return AdminAuditCollection;
});
