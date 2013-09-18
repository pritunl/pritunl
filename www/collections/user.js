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
      this.org = options.org;
    },
    url: function() {
      return '/user/' + this.org;
    }
  });

  return UserCollection;
});
