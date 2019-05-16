define([
  'jquery',
  'underscore',
  'backbone',
  'views/alert',
  'views/hostUsage',
  'views/modalDeleteHost',
  'views/modalHostSettings',
  'text!templates/hostsListItem.html'
], function($, _, Backbone, AlertView, HostUsageView, ModalDeleteHostView,
    ModalHostSettingsView, hostsListItemTemplate) {
  'use strict';
  var HostListItemView = Backbone.View.extend({
    className: 'host',
    template: _.template(hostsListItemTemplate),
    events: {
      'click .host-title a': 'onSettings',
      'click .host-del': 'onDelete',
      'click .host-cpu-usage-btn': 'onCpuUsageGraph',
      'click .host-mem-usage-btn': 'onMemUsageGraph',
      'click .graph-period': 'onGraphPeriod',
      'click .toggle-hidden': 'onToggleHidden'
    },
    initialize: function() {
      this.hostUsageView = new HostUsageView({
        host: this.model.get('id')
      });
      this.addView(this.hostUsageView);

      setTimeout(function() {
        if (window.disableInterval) {
          return;
        }
        this.uptimer = setInterval((this._updateTime).bind(this), 1000);
      }.bind(this), 1000);
    },
    deinitialize: function() {
      clearInterval(this.uptimer);
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      this.update();
      this.$('.host-graph-viewer').append(
        this.hostUsageView.render().el);
      return this;
    },
    update: function() {
      var name = this.model.get('name');
      var hostname = this.model.get('hostname');
      var version = this.model.get('version');

      if (hostname) {
        name += ' (' + hostname + ')';
      }

      this.$('.host-title a').text(name);
      this.$('.host-status .status-text').text(
        this.model.get('status').charAt(0).toUpperCase() +
        this.model.get('status').slice(1) + (version ? (' (v' +
        version + ')') : ''));
      if (this.model.get('uptime')) {
        this.$('.host-uptime .status-text').text(
          window.formatUptime(this.model.get('uptime')));
      }
      else {
        this.$('.host-uptime .status-text').text('-');
      }
      this.$('.host-users .status-num').text(this.model.get(
        'users_online') + '/' + this.model.get('user_count'));

      if (this.model.get('status') === 'offline') {
        this.$('.host-del').removeAttr('disabled');
      }
      else {
        this.$('.host-del').attr('disabled', 'disabled');
      }

      this.$('.host-public-address .status-text').text(
        this.model.get('public_addr'));
      this.$('.host-local-address .status-text').text(
        this.model.get('local_addr'));
    },
    onCpuUsageGraph: function() {
      this.$('.host-mem-usage-btn').removeClass('btn-primary');
      this.$('.host-mem-usage-btn').addClass('btn-default');
      this.$('.host-cpu-usage-btn').removeClass('btn-default');
      this.$('.host-cpu-usage-btn').addClass('btn-primary');
      this.hostUsageView.setType('cpu');
    },
    onMemUsageGraph: function() {
      this.$('.host-cpu-usage-btn').removeClass('btn-primary');
      this.$('.host-cpu-usage-btn').addClass('btn-default');
      this.$('.host-mem-usage-btn').removeClass('btn-default');
      this.$('.host-mem-usage-btn').addClass('btn-primary');
      this.hostUsageView.setType('mem');
    },
    onSettings: function() {
      this.$('.host-title a').addClass('disabled');

      var modal = new ModalHostSettingsView({
        model: this.model.clone()
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully saved host settings.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);

      this.$('.host-title a').removeClass('disabled');
    },
    onGraphPeriod: function(evt) {
      this.$('.graph-period').removeClass('btn-primary');
      this.$('.graph-period').addClass('btn-default');
      $(evt.target).removeClass('btn-default');
      $(evt.target).addClass('btn-primary');

      if ($(evt.target).hasClass('graph-1m')) {
        this.hostUsageView.setPeriod('1m');
      }
      else if ($(evt.target).hasClass('graph-5m')) {
        this.hostUsageView.setPeriod('5m');
      }
      else if ($(evt.target).hasClass('graph-30m')) {
        this.hostUsageView.setPeriod('30m');
      }
      else if ($(evt.target).hasClass('graph-2h')) {
        this.hostUsageView.setPeriod('2h');
      }
      else if ($(evt.target).hasClass('graph-1d')) {
        this.hostUsageView.setPeriod('1d');
      }
    },
    onDelete: function(evt) {
      var model = this.model.clone();

      if (evt.shiftKey && evt.ctrlKey && evt.altKey) {
        model.destroy();
        return;
      }

      var modal = new ModalDeleteHostView({
        model: model
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully deleted host.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    _updateTime: function() {
      if (!this.model.get('uptime')) {
        return;
      }
      this.model.set({
        uptime: this.model.get('uptime') + 1
      });
      this.$('.host-uptime .status-text').text(
        window.formatUptime(this.model.get('uptime')));
    },
    onToggleHidden: function(evt) {
      if (!evt.ctrlKey && !evt.shiftKey) {
        return;
      }
      if (this.$el.hasClass('show-hidden')) {
        this.$('.toggle-hidden').removeClass('label-warning');
        this.$('.toggle-hidden').addClass('label-danger');
        this.$el.removeClass('show-hidden');
      }
      else {
        this.$('.toggle-hidden').addClass('label-warning');
        this.$('.toggle-hidden').removeClass('label-danger');
        this.$el.addClass('show-hidden');
      }
    }
  });

  return HostListItemView;
});
