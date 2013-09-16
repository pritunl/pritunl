define([
  'jquery',
  'underscore',
  'backbone',
  'models/status',
  'text!templates/dashboardStatus.html'
], function($, _, Backbone, StatusModel, dashboardStatusTemplate) {
  'use strict';
  var DashboardStatusView = Backbone.View.extend({
    className: 'status-container',
    template: _.template(dashboardStatusTemplate),
    initialize: function() {
      this.model = new StatusModel();
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    }
  });

  return DashboardStatusView;
});
