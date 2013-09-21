define([
  'jquery',
  'underscore',
  'backbone',
  'models/server',
  'views/modalServerSettings'
], function($, _, Backbone, ServerModel, ModalServerSettingsView) {
  'use strict';
  var ModalAddServerView = ModalServerSettingsView.extend({
    title: 'Add Server',
    okText: 'Add',
    loadingMsg: 'Adding server...',
    errorMsg: 'Failed to add server, server error occurred.',
    initialize: function() {
      // TODO
      this.events['click .selector'] = 'onSelect';
      this.model = new ServerModel({
        name: '',
        network: '10.' + this._rand(15, 250) + '.' +
          this._rand(15, 250) + '.0/24',
        interface: this._get_free_interface(),
        port: this._rand(10000, 19999),
        protocol: 'udp'
      });
      this.body = this.template(this.model.toJSON());
      this.render();
    },
    _rand: function(min, max) {
      return Math.floor(Math.random() * (max - min + 1)) + min;
    },
    _get_free_interface: function() {
      var i;
      var iface;
      var ifaces = [];
      $('.server .server-interface .status-text').each(function() {
        ifaces.push($(this).text());
      });

      for (var i = 0; i < 64; i++) {
        iface = 'tun' + i;
        if (ifaces.indexOf(iface) === -1) {
          break;
        }
      }

      return iface;
    },
    onRemove: function() {
      if (!this.triggerEvt) {
        return;
      }
      this.trigger('added');
    }
  });

  return ModalAddServerView;
});
