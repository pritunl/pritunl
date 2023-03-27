define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var UserDeviceModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'user_id': null,
      'org_id': null,
      'name': null,
      'registered': null,
      'timestamp': null
    },
    url: function() {
      return '/user/' + this.get('org_id') + '/' + this.get('user_id') +
        '/device/' + this.get('id');
    }
  });

  return UserDeviceModel;
});
