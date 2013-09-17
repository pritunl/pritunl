define([
  'jquery',
  'underscore',
  'backbone',
  'views/dashboardStatus',
  'text!templates/dashboard.html'
], function($, _, Backbone, DashboardStatus, dashboardTemplate) {
  'use strict';
  var DashboardView = Backbone.View.extend({
    className: 'dashboard container',
    template: _.template(dashboardTemplate),
    initialize: function() {
      this.children = [];
      this.dashboardStatusView = new DashboardStatus();
      this.children.push(this.dashboardStatusView);
    },
    render: function() {
      this.$el.html(this.template());
      this.$el.prepend(this.dashboardStatusView.render().el);
      return this;
    }
  });

  return DashboardView;
});
