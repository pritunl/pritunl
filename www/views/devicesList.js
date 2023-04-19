define([
  'jquery',
  'underscore',
  'backbone',
  'collections/device',
  'views/list',
  'views/alert',
  'views/devicesListItem',
  'text!templates/devicesList.html'
], function($, _, Backbone, DevicesCollection, ListView, AlertView,
    DevicesListItemView, devicesListTemplate) {
  'use strict';
  var DevicesListView = ListView.extend({
    listContainer: '.devices-list-container',
    template: _.template(devicesListTemplate),
    listErrorMsg: 'Failed to load unregistered devices, ' +
      'server error occurred.',
    initialize: function() {
      this.collection = new DevicesCollection();
      this.listenTo(window.events, 'devices_updated', this.update);
      DevicesListView.__super__.initialize.call(this);
    },
    buildItem: function(model) {
      return new DevicesListItemView({
        model: model
      });
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

  return DevicesListView;
});
