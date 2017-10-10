define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var UserAuditModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'user_id': null,
      'org_id': null,
      'timestamp': null,
      'type': null,
      'remote_addr': null,
      'message': null
    },
    url: function() {
      return null;
    }
  });

  return UserAuditModel;
});
