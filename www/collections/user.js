define([
  'jquery',
  'underscore',
  'backbone',
  'models/user'
], function($, _, Backbone, UserModel) {
  'use strict';
  var UserCollection = Backbone.Collection.extend({
    model: UserModel,
    url: function() {
      return '/user';
    }
  });

  return UserCollection;
});
