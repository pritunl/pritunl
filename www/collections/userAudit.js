define([
  'jquery',
  'underscore',
  'backbone',
  'models/userAudit'
], function($, _, Backbone, UserAuditModel) {
  'use strict';
  var UserAuditCollection = Backbone.Collection.extend({
    model: UserAuditModel,
    initialize: function(options) {
      this.user = options.user;
    },
    url: function() {
      return '/user/' + this.user.get('organization') + '/' +
        this.user.get('id') + '/audit';
    }
  });

  return UserAuditCollection;
});
