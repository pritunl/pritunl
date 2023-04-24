define([
  'jquery',
  'underscore',
  'backbone',
  'collections/userDevice',
  'views/list',
  'views/userDevicesListItem',
  'text!templates/userDevicesList.html'
], function($, _, Backbone, UserDeviceCollection, ListView,
    UserDevicesListItemView, userDevicesListTemplate) {
  'use strict';
  var DeviceDevicesListView = ListView.extend({
    className: 'user-devices-container',
    listContainer: '.user-devices',
    template: _.template(userDevicesListTemplate),
    listErrorMsg: 'Failed to load user information, ' +
      'server error occurred.',
    initialize: function(options) {
      this.models = options.models;
      this.collection = new UserDeviceCollection();
      DeviceDevicesListView.__super__.initialize.call(this);
    },
    buildItem: function(model) {
      return new UserDevicesListItemView({
        model: model
      });
    },
    update: function(models) {
      if (models === undefined) {
        models = this.models;
      }
      this.collection.reset(models);
    },
    resetItems: function(views) {
      if (!views.length) {
        this.$('.no-devices').slideDown(window.slideTime);
      }
      else {
        this.$('.no-devices').slideUp(window.slideTime);
      }
    }
  });

  return DeviceDevicesListView;
});
