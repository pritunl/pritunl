define([
  'jquery',
  'underscore',
  'backbone',
  'models/status',
  'views/alert',
  'views/modalNotification',
  'text!templates/dashboardStatus.html'
], function($, _, Backbone, StatusModel, AlertView, ModalNotificationView,
    dashboardStatusTemplate) {
  'use strict';
  var DashboardStatusView = Backbone.View.extend({
    className: 'status-container',
    template: _.template(dashboardStatusTemplate),
    initialize: function() {
      this.notified = false;
      this.model = new StatusModel();
      this.listenTo(window.events, 'users_updated', this.update);
      this.listenTo(window.events, 'organizations_updated', this.update);
      this.listenTo(window.events, 'servers_updated', this.update);
    },
    onNotification: function() {
      if (this.notified) {
        return;
      }
      this.notified = true;
      var modal = new ModalNotificationView({
        model: this.model.clone()
      });
      this.addView(modal);
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
          this.$(selectors).removeClass(
            'default-text warning-text success-text');
          this.$(selectors).addClass('error-text');

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

          if (this.model.get('notification')) {
            this.onNotification();
          }

          num = this.model.get('org_count');
          if (num === 0) {
            num = '-';
            this.$('.orgs-status .status-num').removeClass(
              'error-text warning-text success-text');
            this.$('.orgs-status .status-num').addClass('default-text');
          }
          else {
            this.$('.orgs-status .status-num').removeClass(
              'default-text error-text warning-text');
            this.$('.orgs-status .status-num').addClass('success-text');
          }
          this.$('.orgs-status .status-num').text(num + '/' + num);

          num = this.model.get('users_online');
          totalNum = this.model.get('user_count');
          if (num === 0) {
            if (totalNum === 0) {
              num = '-';
              totalNum = '-';
            }
            this.$('.users-status .status-num').removeClass(
              'error-text warning-text success-text');
            this.$('.users-status .status-num').addClass('default-text');
          }
          else {
            this.$('.users-status .status-num').removeClass(
              'default-text error-text warning-text');
            this.$('.users-status .status-num').addClass('success-text');
          }
          this.$('.users-status .status-num').text(num + '/' + totalNum);

          num = this.model.get('servers_online');
          totalNum = this.model.get('server_count');
          if (totalNum === 0) {
            num = '-';
            totalNum = '-';
            this.$('.servers-status .status-num').removeClass(
              'error-text warning-text success-text');
            this.$('.servers-status .status-num').addClass('default-text');
          }
          else if (num === 0) {
            this.$('.servers-status .status-num').removeClass(
              'default-text warning-text success-text');
            this.$('.servers-status .status-num').addClass('error-text');
          }
          else if (num < totalNum) {
            this.$('.servers-status .status-num').removeClass(
              'default-text error-text success-text');
            this.$('.servers-status .status-num').addClass('warning-text');
          }
          else {
            this.$('.servers-status .status-num').removeClass(
              'default-text error-text warning-text');
            this.$('.servers-status .status-num').addClass('success-text');
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
