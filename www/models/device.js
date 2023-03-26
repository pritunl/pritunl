define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var DeviceModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'org_id': null,
      'user_id': null,
      'user_name': null,
      'name': null,
      'platform': null,
      'reg_key': null
    },
    url: function() {
      return '/device/register/' + this.get('org_id') + '/' +
        this.get('user_id') + '/' + this.get('id');
    }
  });

  return DeviceModel;
});
