define([
  'jquery',
  'underscore',
  'backbone',
  'collections/log',
  'views/list',
  'views/dashboardLogItem',
  'text!templates/dashboardLog.html'
], function($, _, Backbone, LogCollection, ListView, DashboardLogItemView,
    dashboardLogTemplate) {
  'use strict';
  var DashboardLogView = ListView.extend({
    className: 'log-container',
    listContainer: '.log-entry-list',
    listErrorMsg: 'Failed to load log entries, server error occurred.',
    template: _.template(dashboardLogTemplate),
    initialize: function() {
      this.collection = new LogCollection();
      this.listenTo(window.events, 'log_updated', this.update);
      DashboardLogView.__super__.initialize.call(this);
    },
    buildItem: function(model) {
      var modelView = new DashboardLogItemView({
        model: model
      });
      return modelView;
    },
    resetItems: function(views) {
      if (views.length) {
        this.$('.last').removeClass('last');
        views[views.length - 1].$el.addClass('last');
      }
    }
  });

  return DashboardLogView;
});
