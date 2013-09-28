define([
  'jquery',
  'underscore',
  'backbone',
  'views/alert',
  'views/serverOrgsList',
  'views/serverOutput',
  'views/modalServerSettings',
  'views/modalDeleteServer',
  'text!templates/serversListItem.html'
], function($, _, Backbone, AlertView, ServerOrgsListView, ServerOutputView,
    ModalServerSettingsView, ModalDeleteServerView, serversListItemTemplate) {
  'use strict';
  var ServersListItemView = Backbone.View.extend({
    className: 'server',
    template: _.template(serversListItemTemplate),
    events: {
      'click .server-title a': 'onSettings',
      'click .server-del': 'onDelete',
      'click .server-restart, .server-start, .server-stop': 'onOperation',
      'click .server-output-clear': 'onClearOutput'
    },
    initialize: function() {
      this.serverOrgsListView = new ServerOrgsListView({
        server: this.model.get('id')
      });
      this.addView(this.serverOrgsListView);
      this.serverOutputView = new ServerOutputView({
        server: this.model.get('id')
      });
      this.addView(this.serverOutputView);
      setTimeout((this._updateTime).bind(this), 1000);
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      this.update();
      this.$('.server-title a, .server-output-clear').tooltip({
        container: this.el
      });
      this.$('.server-output-viewer').append(
        this.serverOutputView.render().el);
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
      this.$('.server-public-address .status-text').text(
        this.model.get('public_address'));

      if (!this.model.get('org_count')) {
        this.$('.server-stop').hide();
        this.$('.server-start').show();
        this.startDisabled = true;
        this.$('.server-start').attr('disabled', 'disabled');
        this.restartDisabled = true;
        this.$('.server-restart').attr('disabled', 'disabled');
      }
      else if (this.model.get('status') === 'online') {
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
    onOperation: function(evt) {
      var operation;
      var operationPastTense;

      if ($(evt.target).hasClass('server-restart')) {
        operation = 'restart';
        operationPastTense = 'restarted';
      }
      else if ($(evt.target).hasClass('server-start')) {
        operation = 'start';
        operationPastTense = 'started';
      }
      else if ($(evt.target).hasClass('server-stop')) {
        operation = 'stop';
        operationPastTense = 'stopped';
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
          var alertView = new AlertView({
            type: 'warning',
            message: 'Successfully ' + operationPastTense + ' the server.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
        }.bind(this),
        error: function() {
          $(evt.target).removeAttr('disabled');
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to ' + operation +
              ' the server, server error occurred.',
            dismissable: true
          });
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
