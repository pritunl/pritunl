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
    loadingMsg: 'Adding server, this will take several minutes...',
    errorMsg: 'Failed to add server, server error occurred.',
    initialize: function(options) {
      this.model = new ServerModel({
        'name': '',
        'type': options.type,
        'network': '10.' + this._rand(15, 250) + '.' +
          this._rand(15, 250) + '.0/24',
        'interface': this._get_free_interface(),
        'port': this._rand(10000, 19999),
        'protocol': 'udp',
        'public_address': options.publicIp || '',
        'local_networks': []
      });
      this.constructor.__super__.initialize.call(this, options);
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

      for (i = 0; i < 64; i++) {
        iface = 'tun' + i;
        if (ifaces.indexOf(iface) === -1) {
          break;
        }
      }

      return iface;
    }
  });

  return ModalAddServerView;
});
