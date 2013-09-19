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
    template: _.template(dashboardLogTemplate),
    init: function() {
      this.collection = new LogCollection();
    },
    buildItem: function(model) {
      var modelView = new DashboardLogItemView({
        model: model
      });
      return modelView;
    },
    resetItems: function(views) {
      if (this.views.length) {
        this.$('.last').removeClass('last');
        this.views[this.views.length - 1].$el.addClass('last');
      }
    },
    update: function() {
      this.collection.reset([
        {
          'id': 'd5d860c2a5af48e2933e42119be5f43c',
          'date': '03:57 pm - Sep 15, 2013',
          'message': 'Deleted users.'
        },
        {
          'id': '8d7701a94bd74facb49f9e17fee167a7',
          'date': '03:45 pm - Sep 15, 2013',
          'message': 'Created new user.'
        },
        {
          'id': '47215fea69984943a495ae753aa30d0e',
          'date': '03:42 pm - Sep 15, 2013',
          'message': 'Created new user.'
        },
        {
          'id': 'd4f574b8a8ac492e9567701b3f2e61a4',
          'date': '03:38 pm - Sep 15, 2013',
          'message': 'Deleted users.'
        },
        {
          'id': '862a2e45265f41b296e2b5398a7c0456',
          'date': '03:35 pm - Sep 15, 2013',
          'message': 'Created new user.'
        },
        {
          'id': 'b71c8e01d59541bda2e8efb4a5cccffc',
          'date': '03:32 pm - Sep 15, 2013',
          'message': 'Deleted users.'
        },
        {
          'id': '3dcae23770414aceaecc8a496d499aa8',
          'date': '03:23 pm - Sep 15, 2013',
          'message': 'Created new user.'
        },
        {
          'id': 'a8df39ca6e2d4ebe8e538dc4a6fa5a96',
          'date': '03:14 pm - Sep 15, 2013',
          'message': 'Deleted users.'
        },
        {
          'id': '2b97bbf1f7914444bdb0f20c2b6c1364',
          'date': '03:11 pm - Sep 15, 2013',
          'message': 'Created new user.'
        },
        {
          'id': '89436addc66442bf8604dc45fe2eaf0f',
          'date': '03:03 pm - Sep 15, 2013',
          'message': 'Created new organization.'
        }
      ]);
    }
  });

  return DashboardLogView;
});
