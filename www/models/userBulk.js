define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var UserBulkModel = Backbone.Model.extend({
    defaults: {
      'organization': null,
      'users': null
    },
    initialize: function() {
      this.set({'users': []});
    },
    url: function() {
      return '/user/' + this.get('organization') + '/multi';
    },
    toJSON: function() {
      return this.get('users');
    },
    addUser: function(name, email) {
      var users = this.get('users');
      users.push({
        'name': name,
        'email': email || null,
      });
    }
  });

  return UserBulkModel;
});
