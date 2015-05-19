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
      this.listenTo(window.events, 'hosts_updated', this.update);
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
          this.$('.hosts-status .status-num').text('-/-');

          var selectors = '.orgs-status .status-num, ' +
            '.users-status .status-num, ' +
            '.servers-status .status-num' +
            '.hosts-status .status-num';
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
          var i;
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

          var type;
          var types = ['server', 'host'];
          for (i = 0; i < types.length; i++) {
            type = types[i];
            num = this.model.get(type + 's_online');
            totalNum = this.model.get(type + '_count');
            if (totalNum === 0) {
              num = '-';
              totalNum = '-';
              this.$('.' + type + 's-status .status-num').removeClass(
                'error-text warning-text success-text');
              this.$('.' + type + 's-status .status-num').addClass(
                'default-text');
            }
            else if (num === 0) {
              this.$('.' + type + 's-status .status-num').removeClass(
                'default-text warning-text success-text');
              this.$('.' + type + 's-status .status-num').addClass(
                'error-text');
            }
            else if (num < totalNum) {
              this.$('.' + type + 's-status .status-num').removeClass(
                'default-text error-text success-text');
              this.$('.' + type + 's-status .status-num').addClass(
                'warning-text');
            }
            else {
              this.$('.' + type + 's-status .status-num').removeClass(
                'default-text error-text warning-text');
              this.$('.' + type + 's-status .status-num').addClass(
                'success-text');
            }
            this.$('.' + type + 's-status .status-num').text(
              num + '/' + totalNum);
          }

          var serverInfo = '';
          if (this.model.get('server_version')) {
            serverInfo += 'v' + this.model.get('server_version');
          }
          if (this.model.get('current_host')) {
            if (serverInfo) {
              serverInfo += ' ';
            }
            serverInfo += this.model.get('current_host').substr(0, 6);
          }
          this.$('.server-info').text(serverInfo);
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
