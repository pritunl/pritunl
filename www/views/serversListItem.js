define([
  'jquery',
  'underscore',
  'backbone',
  'models/status',
  'views/alert',
  'views/serverOrgsList',
  'views/serverOutput',
  'views/serverBandwidth',
  'views/modalServerSettings',
  'views/modalDeleteServer',
  'text!templates/serversListItem.html'
], function($, _, Backbone, StatusModel, AlertView, ServerOrgsListView,
    ServerOutputView, ServerBandwidthView, ModalServerSettingsView,
    ModalDeleteServerView, serversListItemTemplate) {
  'use strict';
  var ServersListItemView = Backbone.View.extend({
    className: 'server',
    template: _.template(serversListItemTemplate),
    events: {
      'click .server-title a': 'onSettings',
      'click .server-del': 'onDelete',
      'click .server-restart, .server-start, .server-stop': 'onOperation',
      'click .server-output-btn': 'onServerOutput',
      'click .server-graph-btn': 'onServerGraph',
      'click .server-output-clear': 'onClearOutput',
      'click .server-graph-period': 'onServerGraphPeriod',
      'click .toggle-hidden': 'onToggleHidden'
    },
    initialize: function() {
      this.statusModel = new StatusModel();
      this.serverOrgsListView = new ServerOrgsListView({
        server: this.model
      });
      this.addView(this.serverOrgsListView);
      this.serverOutputView = new ServerOutputView({
        server: this.model.get('id')
      });
      this.addView(this.serverOutputView);
      this.serverBandwidthView = new ServerBandwidthView({
        server: this.model.get('id')
      });
      this.addView(this.serverBandwidthView);
      setTimeout(function() {
        this.uptimer = setInterval((this._updateTime).bind(this), 1000);
      }.bind(this), 1000);
    },
    deinitialize: function() {
      clearInterval(this.uptimer);
    },
    formatDate: function(epochTime) {
        var dateString = new Date(epochTime * 1000).toUTCString();
        var dateArray = dateString.split(' ');
        dateArray[0] = dateArray[0].replace(',', '');

        return dateArray[2] + ', ' + dateArray[1] + ' ' + dateArray[3];
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      this.update();
      this.$('.server-title a, .server-output-clear').tooltip({
        container: this.el
      });
      this.$('.server-output-viewer').append(
        this.serverOutputView.render().el);
      this.$('.server-graph-viewer').append(
        this.serverBandwidthView.render().el);
      this.$el.append(this.serverOrgsListView.render().el);

      if (this.model.get('type') === 'node_server') {
        this.$('.server-label').hide();
        this.$el.addClass('node-server');
        this.$('.server-public-address').removeClass('last');
      }
      else {
        this.$('.node-label').hide();
        this.$('.server-node-host').hide();
      }

      return this;
    },
    update: function() {
      this.$('.server-title a').text(this.model.get('name'));
      this.$('.server-status .status-text').text(
        this.model.get('status') ? 'Online' : 'Offline');
      if (this.model.get('uptime')) {
        this.$('.server-uptime .status-text').text(
          window.formatUptime(this.model.get('uptime')));
      }
      else {
        this.$('.server-uptime .status-text').text('-');
      }
      if (this.model.get('user_count') === 0) {
        this.$('.server-users .status-num').text('-/-');
      }
      else {
        this.$('.server-users .status-num').text(this.model.get(
          'users_online') + '/' + this.model.get('user_count'));
      }
      this.$('.server-network .status-text').text(
        this.model.get('network'));
      this.$('.server-interface .status-text').text(
        this.model.get('interface'));
      this.$('.server-port .status-text').text(
        this.model.get('port') + '/' + this.model.get('protocol'));
      this.$('.server-public-address .status-text').text(
        this.model.get('public_address'));
      this.$('.server-node-host .status-text').text(
        this.model.get('node_host'));

      if (!this.model.get('org_count')) {
        this.$('.server-stop').hide();
        this.$('.server-start').show();
        this.startDisabled = true;
        this.restartDisabled = true;
        this.$('.server-start, .server-restart').attr('disabled', 'disabled');
        this.$('.no-org-warning').show();
      }
      else if (this.model.get('status')) {
        this.$('.server-start').hide();
        this.$('.server-stop').show();
        // Starting and restarting server will also disable buttons
        // only remove disabled if originally done above
        if (this.startDisabled) {
          this.startDisabled = false;
          this.$('.server-start').removeAttr('disabled');
        }
        if (this.restartDisabled) {
          this.startDisabled = false;
          this.$('.server-restart').removeAttr('disabled');
        }
        this.$('.no-org-warning').hide();
      }
      else {
        this.$('.server-stop').hide();
        this.$('.server-start').show();
        if (this.startDisabled) {
          this.startDisabled = false;
          this.$('.server-start').removeAttr('disabled');
        }
        this.restartDisabled = true;
        this.$('.server-restart').attr('disabled', 'disabled');
        this.$('.no-org-warning').hide();
      }
    },
    onSettings: function() {
      if (this.model.get('status')) {
        var alertView = new AlertView({
          type: 'danger',
          message: 'Server must be offline to modify settings.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        return;
      }
      this.$('.server-title a').addClass('disabled');
      this.statusModel.fetch({
        success: function() {
          var modal = new ModalServerSettingsView({
            localNetworks: this.statusModel.get('local_networks'),
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
          this.$('.server-title a').removeClass('disabled');
        }.bind(this),
        error: function() {
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to load server information, ' +
              'server error occurred.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
          this.$('.server-title a').removeClass('disabled');
        }.bind(this)
      });
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
    onOperation: function(evt) {
      var operation;

      if ($(evt.target).hasClass('server-restart')) {
        operation = 'restart';
      }
      else if ($(evt.target).hasClass('server-start')) {
        operation = 'start';
      }
      else if ($(evt.target).hasClass('server-stop')) {
        operation = 'stop';
      }
      if (!operation) {
        return;
      }

      $(evt.target).attr('disabled', 'disabled');
      this.model.clone().save({
        operation: operation
      }, {
        success: function() {
          $(evt.target).removeAttr('disabled');
        }.bind(this),
        error: function(model, response) {
          var alertView;
          $(evt.target).removeAttr('disabled');
          if (response.responseJSON) {
            alertView = new AlertView({
              type: 'danger',
              message: response.responseJSON.error_msg,
              dismissable: true
            });
          }
          else {
            alertView = new AlertView({
              type: 'danger',
              message: 'Failed to ' + operation +
                ' the server, server error occurred.',
              dismissable: true
            });
          }
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
        }.bind(this)
      });
    },
    onClearOutput: function() {
      this.serverOutputView.model.destroy({
        error: function() {
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to clear server output, server error occurred.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
        }.bind(this)
      });
    },
    onServerGraphPeriod: function(evt) {
      this.$('.server-graph-period').removeClass('btn-primary');
      this.$('.server-graph-period').addClass('btn-default');
      $(evt.target).removeClass('btn-default');
      $(evt.target).addClass('btn-primary');

      if ($(evt.target).hasClass('graph-1m')) {
        this.serverBandwidthView.setPeriod('1m');
      }
      else if ($(evt.target).hasClass('graph-5m')) {
        this.serverBandwidthView.setPeriod('5m');
      }
      else if ($(evt.target).hasClass('graph-30m')) {
        this.serverBandwidthView.setPeriod('30m');
      }
      else if ($(evt.target).hasClass('graph-2h')) {
        this.serverBandwidthView.setPeriod('2h');
      }
      else if ($(evt.target).hasClass('graph-1d')) {
        this.serverBandwidthView.setPeriod('1d');
      }
    },
    onServerOutput: function() {
      this.$('.server-output-btn').removeClass('btn-default');
      this.$('.server-output-btn').addClass('btn-primary');
      this.$('.server-graph-btn').removeClass('btn-primary');
      this.$('.server-graph-btn').addClass('btn-default');
      this.$('.server-graph-period').hide();
      this.$('.server-output-clear').show();
      this.serverBandwidthView.setState(false);
      this.serverOutputView.setState(true);
    },
    onServerGraph: function() {
      if (!window.enterprise) {
        return;
      }
      this.$('.server-output-btn').removeClass('btn-primary');
      this.$('.server-output-btn').addClass('btn-default');
      this.$('.server-graph-btn').removeClass('btn-default');
      this.$('.server-graph-btn').addClass('btn-primary');
      this.$('.server-output-clear').hide();
      this.$('.server-graph-period').show();
      this.serverOutputView.setState(false);
      this.serverBandwidthView.setState(true);
    },
    _updateTime: function() {
      if (!this.model.get('uptime')) {
        return;
      }
      this.model.set({
        uptime: this.model.get('uptime') + 1
      });
      this.$('.server-uptime .status-text').text(
        window.formatUptime(this.model.get('uptime')));
    },
    onToggleHidden: function(evt) {
      if (!evt.ctrlKey && !evt.shiftKey) {
        return;
      }
      if (this.$el.hasClass('show-hidden')) {
        this.$('.toggle-hidden').removeClass('label-success');
        this.$('.toggle-hidden').addClass('label-primary');
        this.$el.removeClass('show-hidden');
      }
      else {
        this.$('.toggle-hidden').addClass('label-success');
        this.$('.toggle-hidden').removeClass('label-primary');
        this.$el.addClass('show-hidden');
      }
    }
  });

  return ServersListItemView;
});
