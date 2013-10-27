define([
  'jquery',
  'underscore',
  'backbone',
  'models/key',
  'views/modalRenameUser',
  'views/modalKeyLink',
  'text!templates/usersListItem.html'
], function($, _, Backbone, KeyModel, ModalRenameUserView, ModalKeyLinkView,
    usersListItemTemplate) {
  'use strict';
  var UsersListItemView = Backbone.View.extend({
    className: 'user',
    template: _.template(usersListItemTemplate),
    events: {
      'click .selector': 'onSelect',
      'click .user-name': 'onRename',
      'click .get-key-link': 'onGetKeyLink'
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
        bytesReceived += parseInt(servers[serverId].bytes_received, 10);
      }

      return bytesReceived;
    },
    getBytesSent: function() {
      var serverId;
      var servers = this.model.get('servers');
      var bytesSent = 0;

      for (serverId in servers) {
        bytesSent += parseInt(servers[serverId].bytes_sent, 10);
      }

      return bytesSent;
    },
    _getTooltipText: function() {
      var bytesReceived = this.getBytesReceived();
      var bytesSent = this.getBytesSent();
      var virtAddresses = this.getVirtAddresses();
      if (!virtAddresses.length) {
        return '';
      }
      var tooltipText = 'IP Address: ' + virtAddresses.join(', ');
      tooltipText += '\nBytes Received: ' + bytesReceived;
      tooltipText += '\nBytes Sent: ' + bytesSent;
      return tooltipText;
    },
    render: function() {
      this.$el.html(this.template(_.extend(
        {'tooltip_text': this._getTooltipText()}, this.model.toJSON())));
      this.$('[data-toggle="tooltip"]').tooltip();
      if (this.model.get('type') !== 'client') {
        this.hidden = true;
      }
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
      var virtAddresses = this.getVirtAddresses();
      this.$('.status-container').tooltip('destroy');
      this.$('.status-container').attr('title', this._getTooltipText());
      this.$('.status-container').attr('data-original-title',
        this._getTooltipText());
      this.$('.status-container').tooltip();
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
      if (window.demo) {
        return;
      }
      var modal = new ModalKeyLinkView({
        model: new KeyModel({
          'organization': this.model.get('organization'),
          'user': this.model.get('id')
        })
      });
      this.addView(modal);
    }
  });

  return UsersListItemView;
});
