define([
  'jquery',
  'underscore',
  'backbone',
  'models/userDevice'
], function($, _, Backbone, UserDeviceModel) {
  'use strict';
  var UserDeviceCollection = Backbone.Collection.extend({
    model: UserDeviceModel
  });

  return UserDeviceCollection;
});
