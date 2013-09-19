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
      this.listenTo(window.events, 'users_updated', this.update);
      this.listenTo(window.events, 'organizations_updated', this.update);
    },
    update: function() {
      this.model.fetch({
        error: function() {
          this.$('.orgs-status .status-num').text('-/-');
          this.$('.users-status .status-num').text('-/-');
          this.$('.servers-status .status-num').text('-/-');
        }.bind(this),
        success: function() {
          this.$('.orgs-status .status-num').text(
            this.model.get('orgs_available') + '/' +
            this.model.get('orgs_total'));
          this.$('.users-status .status-num').text(
            this.model.get('users_online') + '/' +
            this.model.get('users_total'));
          this.$('.servers-status .status-num').text(
            this.model.get('servers_online') + '/' +
            this.model.get('servers_total'));
        }.bind(this)
      });
    },
    render: function() {
      this.$el.html(this.template());
      this.update();
      return this;
    }
  });

  return DashboardStatusView;
});
