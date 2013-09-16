define([
  'jquery',
  'underscore',
  'backbone',
  'text!templates/dashboardStatus.html'
], function($, _, Backbone, dashboardStatusTemplate) {
  'use strict';
  var DashboardStatusView = Backbone.View.extend({
    className: 'status-container'
    template: _.template(dashboardStatusTemplate),
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    }
  });

  return DashboardStatusView;
});
