define([
  'jquery',
  'underscore',
  'backbone',
  'views/dashboardStatus',
  'views/dashboardLog',
  'text!templates/dashboard.html'
], function($, _, Backbone, DashboardStatusView, DashboardLogView,
    dashboardTemplate) {
  'use strict';
  var DashboardView = Backbone.View.extend({
    className: 'dashboard container',
    template: _.template(dashboardTemplate),
    initialize: function() {
      this.dashboardStatusView = new DashboardStatusView();
      this.addView(this.dashboardStatusView);
      this.dashboardLogView = new DashboardLogView();
      this.addView(this.dashboardLogView);
    },
    render: function() {
      this.$el.html(this.template());
      this.$el.prepend(this.dashboardStatusView.render().el);
      this.$el.append(this.dashboardLogView.render().el);
      return this;
    }
  });

  return DashboardView;
});
