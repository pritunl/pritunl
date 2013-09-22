define([
  'jquery',
  'underscore',
  'backbone',
  'views/alert',
  'views/serverOrgsList',
  'views/modalServerSettings',
  'views/modalDeleteServer',
  'text!templates/serversListItem.html'
], function($, _, Backbone, AlertView, ServerOrgsListView,
    ModalServerSettingsView, ModalDeleteServerView, serversListItemTemplate) {
  'use strict';
  var ServersListItemView = Backbone.View.extend({
    className: 'server',
    template: _.template(serversListItemTemplate),
    events: {
      'click .server-title a': 'onSettings',
      'click .server-del': 'onDelete'
    },
    initialize: function() {
      this.serverOrgsListView = new ServerOrgsListView({
        server: this.model.get('id')
      });
      this.addView(this.serverOrgsListView);
      setTimeout((this._updateTime).bind(this), 1000);
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      this.update();
      this.$('.server-title a').tooltip({
        container: this.el
      });
      this.$el.append(this.serverOrgsListView.render().el);
      return this;
    },
    update: function() {
      this.$('.server-title a').text(this.model.get('name'));
      var status = this.model.get('status');
      status = status.charAt(0).toUpperCase() + status.slice(1);
      this.$('.server-status .status-text').text(status);
      if (this.model.get('uptime')) {
        this.$('.server-uptime .status-text').text(
          window.formatUptime(this.model.get('uptime')));
      }
      else {
        this.$('.server-uptime .status-text').text('-');
      }
      this.$('.server-users .status-num').text(
        this.model.get('users_online') + '/' + this.model.get('users_total'));
      this.$('.server-network .status-text').text(
        this.model.get('network'));
      this.$('.server-interface .status-text').text(
        this.model.get('interface'));
      this.$('.server-port .status-text').text(
        this.model.get('port') + '/' + this.model.get('protocol'));

      if (this.model.get('status') === 'online') {
        this.$('.server-start').hide();
        this.$('.server-stop').show();
        this.$('.server-restart').removeAttr('disabled');
      }
      else {
        this.$('.server-stop').hide();
        this.$('.server-start').show();
        this.$('.server-restart').attr('disabled', 'disabled');
      }
    },
    onSettings: function() {
      var modal = new ModalServerSettingsView({
        model: this.model.clone()
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'warning',
          message: 'Successfully saved server settings.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    onDelete: function() {
      var modal = new ModalDeleteServerView({
        model: this.model.clone()
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'warning',
          message: 'Successfully deleted server.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    _updateTime: function() {
      setTimeout((this._updateTime).bind(this), 1000);
      if (!this.model.get('uptime')) {
        return;
      }
      this.model.set({
        uptime: this.model.get('uptime') + 1
      });
      this.$('.server-uptime .status-text').text(
        window.formatUptime(this.model.get('uptime')));
    }
  });

  return ServersListItemView;
});
