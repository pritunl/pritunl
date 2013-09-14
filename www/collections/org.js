define([
  'jquery',
  'underscore',
  'backbone',
  'models/org'
], function($, _, Backbone, OrgModel) {
  'use strict';
  var OrgCollection = Backbone.Collection.extend({
    model: OrgModel,
    url: function() {
      return '/organizations';
    }
  });

  return OrgCollection;
});
