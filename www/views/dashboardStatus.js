define([
  'jquery',
  'underscore',
  'backbone',
  'models/status',
  'views/alert',
  'text!templates/dashboardStatus.html'
], function($, _, Backbone, StatusModel, AlertView, dashboardStatusTemplate) {
  'use strict';
  var DashboardStatusView = Backbone.View.extend({
    className: 'status-container',
    template: _.template(dashboardStatusTemplate),
    initialize: function() {
      this.model = new StatusModel();
      this.listenTo(window.events, 'users_updated', this.update);
      this.listenTo(window.events, 'organizations_updated', this.update);
      this.listenTo(window.events, 'servers_updated', this.update);
    },
    update: function() {
      this.model.fetch({
        error: function() {
          this.$('.orgs-status .status-num').text('-/-');
          this.$('.users-status .status-num').text('-/-');
          this.$('.servers-status .status-num').text('-/-');

          var selectors = '.orgs-status .status-num, ' +
            '.users-status .status-num, ' +
            '.servers-status .status-num';
          this.$(selectors).removeClass('none warning success');
          this.$(selectors).addClass('error');

          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to load server status, server error occurred.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
        }.bind(this),
        success: function() {
          var num;
          var totalNum;

          num = this.model.get('orgs_available');
          totalNum = this.model.get('orgs_total');
          if (totalNum === 0) {
            num = '-';
            totalNum = '-';
            this.$('.orgs-status .status-num').removeClass(
              'error warning success');
            this.$('.orgs-status .status-num').addClass('none');
          }
          else if (num === 0) {
            this.$('.orgs-status .status-num').removeClass(
              'none warning success');
            this.$('.orgs-status .status-num').addClass('error');
          }
          else if (num < totalNum) {
            this.$('.orgs-status .status-num').removeClass(
              'none error success');
            this.$('.orgs-status .status-num').addClass('warning');
          }
          else {
            this.$('.orgs-status .status-num').removeClass(
              'none error warning');
            this.$('.orgs-status .status-num').addClass('success');
          }
          this.$('.orgs-status .status-num').text(num + '/' + totalNum);

          num = this.model.get('users_online');
          totalNum = this.model.get('users_total');
          if (num === 0) {
            if (totalNum === 0) {
              num = '-';
              totalNum = '-';
            }
            this.$('.users-status .status-num').removeClass(
              'error warning success');
            this.$('.users-status .status-num').addClass('none');
          }
          else {
            this.$('.users-status .status-num').removeClass(
              'none error warning');
            this.$('.users-status .status-num').addClass('success');
          }
          this.$('.users-status .status-num').text(num + '/' + totalNum);

          num = this.model.get('servers_online');
          totalNum = this.model.get('servers_total');
          if (totalNum === 0) {
            num = '-';
            totalNum = '-';
            this.$('.servers-status .status-num').removeClass(
              'error warning success');
            this.$('.servers-status .status-num').addClass('none');
          }
          else if (num === 0) {
            this.$('.servers-status .status-num').removeClass(
              'none warning success');
            this.$('.servers-status .status-num').addClass('error');
          }
          else if (num < totalNum) {
            this.$('.servers-status .status-num').removeClass(
              'none error success');
            this.$('.servers-status .status-num').addClass('warning');
          }
          else {
            this.$('.servers-status .status-num').removeClass(
              'none error warning');
            this.$('.servers-status .status-num').addClass('success');
          }
          this.$('.servers-status .status-num').text(num + '/' + totalNum);

          if (this.model.get('server_version')) {
            this.$('.server-version').text(
              'v' + this.model.get('server_version'));
          }
          else {
            this.$('.server-version').text('');
          }
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
