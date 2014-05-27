define([
  'jquery',
  'underscore',
  'backbone',
  'models/key',
  'views/alert',
  'views/modalRenameUser',
  'views/modalKeyLink',
  'views/modalOtpAuth',
  'views/userServersList',
  'text!templates/usersListItem.html'
], function($, _, Backbone, KeyModel, AlertView, ModalRenameUserView,
    ModalKeyLinkView, ModalOtpAuthView, UserServersListView,
    usersListItemTemplate) {
  'use strict';
  var UsersListItemView = Backbone.View.extend({
    template: _.template(usersListItemTemplate),
    events: {
      'click .selector': 'onSelect',
      'click .user-name': 'onRename',
      'click .get-key-link': 'onGetKeyLink',
      'click .get-otp-auth': 'onGetOtpAuth',
      'click .disable-user': 'onDisableUser',
      'click .enable-user': 'onEnableUser',
      'click .toggle-servers': 'onToggleServers'
    },
    initialize: function() {
      this.serverList = new UserServersListView({
        models: this.model.get('servers')
      });
    },
    getVirtAddresses: function() {
      var i;
      var servers = this.model.get('servers');
      var virtAddresses = [];

      for (i = 0; i < servers.length; i++) {
        if (servers[i].virt_address) {
          virtAddresses.push(servers[i].virt_address);
        }
      }

      return virtAddresses;
    },
    getBytesReceived: function() {
      var i;
      var servers = this.model.get('servers');
      var bytesReceived = 0;

      for (i = 0; i < servers.length; i++) {
        if (servers[i].bytes_received) {
          bytesReceived += servers[i].bytes_received;
        }
      }

      return window.formatSize(bytesReceived);
    },
    getBytesSent: function() {
      var i;
      var servers = this.model.get('servers');
      var bytesSent = 0;

      for (i = 0; i < servers.length; i++) {
        if (servers[i].bytes_sent) {
          bytesSent += servers[i].bytes_sent;
        }
      }

      return window.formatSize(bytesSent);
    },
    _getDownloadTooltip: function() {
      if (this.model.get('has_key')) {
        return 'Click to download key';
      }
      else {
        return 'Organization must be attached to server to download key';
      }
    },
    _getKeyLink: function() {
      if (!this.model.get('has_key')) {
        return '';
      }
      else if (window.demo) {
        return '../key/demo.tar';
      }
      else {
        return '/key/' + this.model.get('organization') + '/' +
          this.model.get('id') + '.tar';
      }
    },
    _getKeyLinkTooltip: function() {
      if (this.model.get('has_key')) {
        return 'Get key links';
      }
      else {
        return 'Organization must be attached to server to get key links';
      }
    },
    render: function() {
      this.$el.html(this.template(_.extend(
        {
          'download_tooltip': this._getDownloadTooltip(),
          'key_link': this._getKeyLink(),
          'key_link_tooltip': this._getKeyLinkTooltip()
        }, this.model.toJSON())));
      this.$('[data-toggle="tooltip"]').tooltip();
      this.$el.append(this.serverList.render().el);
      if (this.model.get('disabled')) {
        this.$('.disable-user').hide();
      }
      else {
        this.$('.enable-user').hide();
      }
      return this;
    },
    update: function() {
      var email = this.model.get('email');
      this.$('.user-name').text(
        this.model.get('name') + (email ? ' (' + email + ')' : ''));
      if (this.model.get('disabled')) {
        this.$('.user .status-icon').removeClass('online');
        this.$('.user .status-icon').removeClass('offline');
        this.$('.user .status-icon').addClass('disabled');
        this.$('.user .status-text').text('Disabled');
        this.$('.disable-user').hide();
        this.$('.enable-user').show();
      }
      else {
        if (this.model.get('status')) {
          this.$('.user .status-icon').removeClass('offline');
          this.$('.user .status-icon').addClass('online');
          this.$('.user .status-text').text('Online');
        }
        else {
          this.$('.user .status-icon').removeClass('online');
          this.$('.user .status-icon').addClass('offline');
          this.$('.user .status-text').text('Offline');
        }
        this.$('.user .status-icon').removeClass('disabled');
        this.$('.enable-user').hide();
        this.$('.disable-user').show();
      }

      this.$('.download-key').tooltip('destroy');
      this.$('.download-key').attr('title', this._getDownloadTooltip());
      this.$('.download-key').attr('data-original-title',
        this._getDownloadTooltip());
      this.$('.download-key').tooltip();

      this.$('.get-key-link').tooltip('destroy');
      this.$('.get-key-link').attr('title', this._getKeyLinkTooltip());
      this.$('.get-key-link').attr('data-original-title',
        this._getKeyLinkTooltip());
      this.$('.get-key-link').tooltip();

      if (this.model.get('otp_auth')) {
        this.$('.right-container').removeClass('no-otp-auth');
        this.$('.get-otp-auth').removeClass('no-otp-auth');
      }
      else {
        this.$('.right-container').addClass('no-otp-auth');
        this.$('.get-otp-auth').addClass('no-otp-auth');
      }

      this.serverList.update(this.model.get('servers'));
    },
    getSelect: function() {
      return this.$('.selector').hasClass('selected');
    },
    setSelect: function(state) {
      if (state) {
        this.$('.selector').addClass('selected');
        this.$('.selector-inner').show();
      }
      else {
        this.$('.selector').removeClass('selected');
        this.$('.selector-inner').hide();
      }
      this.trigger('select', this);
    },
    onSelect: function() {
      this.setSelect(!this.getSelect());
    },
    onRename: function() {
      var modal = new ModalRenameUserView({
        model: this.model.clone()
      });
      this.addView(modal);
    },
    onGetKeyLink: function() {
      if (!this.model.get('has_key')) {
        return;
      }
      var modal = new ModalKeyLinkView({
        model: new KeyModel({
          'organization': this.model.get('organization'),
          'user': this.model.get('id'),
          'otp_auth': this.model.get('otp_auth')
        })
      });
      this.addView(modal);
    },
    onGetOtpAuth: function() {
      var modal = new ModalOtpAuthView({
        model: this.model
      });
      this.addView(modal);
    },
    onDisableUser: function() {
      if (this.$('.disable-user').hasClass('disabled')) {
        return;
      }
      this.$('.disable-user').addClass('disabled');
      this.model.save({
        name: undefined,
        disabled: true
      }, {
        success: function() {
          this.$('.disable-user').removeClass('disabled');
        }.bind(this),
        error: function() {
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to disable user, server error occurred.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
        }.bind(this)
      });
    },
    onEnableUser: function() {
      if (this.$('.enable-user').hasClass('disabled')) {
        return;
      }
      this.$('.enable-user').addClass('disabled');
      this.model.save({
        name: undefined,
        disabled: false
      }, {
        success: function() {
          this.$('.enable-user').removeClass('disabled');
        }.bind(this),
        error: function() {
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to disable user, server error occurred.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
        }.bind(this)
      });
    },
    onToggleServers: function() {
      var tooltipText;
      if (this.$('.toggle-servers').hasClass('glyphicon-chevron-down')) {
        this.$('.toggle-servers').removeClass('glyphicon-chevron-down');
        this.$('.toggle-servers').addClass('glyphicon-chevron-up');
        this.$('.user-servers').slideDown(200);
        tooltipText = 'Hide additional user information';
      }
      else {
        this.$('.toggle-servers').removeClass('glyphicon-chevron-up');
        this.$('.toggle-servers').addClass('glyphicon-chevron-down');
        this.$('.user-servers').slideUp(200);
        tooltipText = 'Show additional user information';
      }

      this.$('.toggle-servers').tooltip('destroy');
      this.$('.toggle-servers').attr('title', tooltipText);
      this.$('.toggle-servers').attr('data-original-title', tooltipText);
      this.$('.toggle-servers').tooltip();
    }
  });

  return UsersListItemView;
});
