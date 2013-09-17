define([
  'jquery',
  'underscore',
  'backbone',
  'views/dashboardStatus',
  'text!templates/dashboard.html'
], function($, _, Backbone, DashboardStatusView, dashboardTemplate) {
  'use strict';
  var DashboardView = Backbone.View.extend({
    className: 'dashboard container',
    template: _.template(dashboardTemplate),
    initialize: function() {
      this.dashboardStatusView = new DashboardStatusView();
      this.addView(this.dashboardStatusView);
    },
    render: function() {
      this.$el.html(this.template());
      this.$el.prepend(this.dashboardStatusView.render().el);
      return this;
    }
  });

  return DashboardView;
});
