define([
  'jquery',
  'underscore',
  'backbone',
  'models/userServer'
], function($, _, Backbone, UserServerModel) {
  'use strict';
  var UserServerCollection = Backbone.Collection.extend({
    model: UserServerModel
  });

  return UserServerCollection;
});
