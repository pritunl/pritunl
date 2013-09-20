define([
  'jquery',
  'underscore',
  'backbone',
  'views/dashboardStatus',
  'views/dashboardLog'
], function($, _, Backbone, DashboardStatusView, DashboardLogView) {
  'use strict';
  var DashboardView = Backbone.View.extend({
    className: 'dashboard container',
    initialize: function() {
      this.dashboardStatusView = new DashboardStatusView();
      this.addView(this.dashboardStatusView);
      this.dashboardLogView = new DashboardLogView();
      this.addView(this.dashboardLogView);
    },
    render: function() {
      this.$el.append(this.dashboardStatusView.render().el);
      this.$el.append(this.dashboardLogView.render().el);
      return this;
    }
  });

  return DashboardView;
});
