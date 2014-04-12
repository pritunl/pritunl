define([
  'jquery',
  'underscore',
  'backbone',
  'models/serverOrg'
], function($, _, Backbone, UserServerModel) {
  'use strict';
  var UserServerCollection = Backbone.Collection.extend({
    model: UserServerModel
  });

  return UserServerCollection;
});
