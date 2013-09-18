define([
  'jquery',
  'underscore',
  'backbone',
  'models/user'
], function($, _, Backbone, UserModel) {
  'use strict';
  var UserCollection = Backbone.Collection.extend({
    model: UserModel,
    initialize: function(options) {
      this.organization = options.organization;
    },
    url: function() {
      return '/user/' + this.organization;
    }
  });

  return UserCollection;
});
