define([
  'jquery',
  'underscore',
  'backbone',
  'models/key',
  'views/modalRenameUser',
  'views/modalKeyLink',
  'views/modalOtpAuth',
  'text!templates/usersListItem.html'
], function($, _, Backbone, KeyModel, ModalRenameUserView, ModalKeyLinkView,
    ModalOtpAuthView, usersListItemTemplate) {
  'use strict';
  var UsersListItemView = Backbone.View.extend({
    className: 'user',
    template: _.template(usersListItemTemplate),
    events: {
      'click .selector': 'onSelect',
      'click .user-name': 'onRename',
      'click .get-key-link': 'onGetKeyLink',
      'click .get-otp-auth': 'onGetOtpAuth'
    },
    getVirtAddresses: function() {
      var serverId;
      var servers = this.model.get('servers');
      var virtAddresses = [];

      for (serverId in servers) {
        virtAddresses.push(servers[serverId].virt_address);
      }

      return virtAddresses;
    },
    getBytesReceived: function() {
      var serverId;
      var servers = this.model.get('servers');
      var bytesReceived = 0;

      for (serverId in servers) {
        bytesReceived += servers[serverId].bytes_received;
      }

      return window.formatSize(bytesReceived);
    },
    getBytesSent: function() {
      var serverId;
      var servers = this.model.get('servers');
      var bytesSent = 0;

      for (serverId in servers) {
        bytesSent += servers[serverId].bytes_sent;
      }

      return window.formatSize(bytesSent);
    },
    _getStatusTooltip: function() {
      var bytesSent = this.getBytesSent();
      var bytesReceived = this.getBytesReceived();
      var virtAddresses = this.getVirtAddresses();
      if (!virtAddresses.length) {
        return '';
      }
      var tooltipText = 'IP Address: ' + virtAddresses.join(', ');
      tooltipText += '\nData Sent: ' + bytesSent;
      tooltipText += '\nData Received: ' + bytesReceived;
      return tooltipText;
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
      if (window.demo) {
        return '../key/demo.tar';
      }
      else if (!this.model.get('has_key')) {
        return '';
      }
      else {
        return '/key/' + this.model.get('organization') + '/' +
          this.model.get('id') + '.tar';
      }
    },
    _getKeyLinkTooltip: function() {
      if (this.model.get('has_key')) {
        return 'Click to generate temporary key url that is downloadable ' +
          'without authenticating';
      }
      else {
        return 'Organization must be attached to server to generate key link';
      }
    },
    render: function() {
      this.$el.html(this.template(_.extend(
        {
          'status_tooltip': this._getStatusTooltip(),
          'download_tooltip': this._getDownloadTooltip(),
          'key_link': this._getKeyLink(),
          'key_link_tooltip': this._getKeyLinkTooltip()
        }, this.model.toJSON())));
      this.$('[data-toggle="tooltip"]').tooltip();
      return this;
    },
    update: function() {
      this.$('.user-name').text(this.model.get('name'));
      if (this.model.get('status')) {
        if (!this.$('.status-icon').hasClass('online')) {
          this.$('.status-icon').removeClass('offline');
          this.$('.status-icon').addClass('online');
          this.$('.status-text').text('Online');
        }
      }
      else {
        if (!this.$('.status-icon').hasClass('offline')) {
          this.$('.status-icon').removeClass('online');
          this.$('.status-icon').addClass('offline');
          this.$('.status-text').text('Offline');
        }
      }

      this.$('.status-container').tooltip('destroy');
      this.$('.status-container').attr('title', this._getStatusTooltip());
      this.$('.status-container').attr('data-original-title',
        this._getStatusTooltip());
      this.$('.status-container').tooltip();

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
    }
  });

  return UsersListItemView;
});
