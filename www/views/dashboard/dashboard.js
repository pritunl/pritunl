define([
  'jquery',
  'underscore',
  'backbone',
  'text!templates/dashboard/dashboard.html'
], function($, _, Backbone, dashboardTemplate) {
  'use strict';
  var DashboardView = Backbone.View.extend({
    template: _.template(dashboardTemplate),
    render: function() {
      this.$el.html(this.template());
      return this;
    }
  });

  return DashboardView;
});
