define([
  'jquery',
  'underscore',
  'backbone',
  'views/alert',
  'views/serverOrgsList',
  'views/modalServerSettings',
  'text!templates/serversListItem.html'
], function($, _, Backbone, AlertView, ServerOrgsListView,
    ModalServerSettingsView, serversListItemTemplate) {
  'use strict';
  var ServersListItemView = Backbone.View.extend({
    className: 'server',
    template: _.template(serversListItemTemplate),
    events: {
      'click .server-title a': 'onSettings'
    },
    initialize: function() {
      this.serverOrgsListView = new ServerOrgsListView({
        server: this.model.get('id')
      });
      this.addView(this.serverOrgsListView);
    },
    onSettings: function() {
      var modal = new ModalServerSettingsView({
        model: this.model.clone()
      });
      this.listenToOnce(modal, 'saved', function() {
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
    update: function() {
      var status = this.model.get('status');
      status = status.charAt(0).toUpperCase() + status.slice(1);
      this.$('.server-status .status-text').text(status);
      this.$('.server-uptime .status-text').text(
        this.model.get('uptime'));
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
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      this.update();
      this.$('.server-title a').tooltip({
        container: this.el
      });
      this.$el.append(this.serverOrgsListView.render().el);
      return this;
    }
  });

  return ServersListItemView;
});
