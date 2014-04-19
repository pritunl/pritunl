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
    safeClose: true,
    initialize: function(options) {
      this.usedNetworks = options.usedNetworks;
      this.usedPorts = options.usedPorts;
      this.usedInterfaces = options.usedInterfaces;

      this.model = new ServerModel({
        'name': '',
        'type': options.type,
        'network': this._get_free_network(),
        'interface': this._get_free_interface(),
        'port': this._get_free_port(),
        'protocol': 'udp',
        'dh_param_bits': 1536,
        'mode': 'all_traffic',
        'public_address': options.publicIp || '',
        'local_networks': [],
        'dns_servers': ['8.8.8.8']
      });
      ModalAddServerView.__super__.initialize.call(this, options);
    },
    _rand: function(min, max) {
      return Math.floor(Math.random() * (max - min + 1)) + min;
    },
    _get_free_network: function() {
      var i;
      var network = '50.203.224.0/24';

      for (i = 0; i < 4096; i++) {
        if (this.usedNetworks.indexOf(network) === -1) {
          break;
        }
        network = '10.' + this._rand(15, 250) + '.' +
          this._rand(15, 250) + '.0/24';
      }

      return network;
    },
    _get_free_port: function() {
      var i;
      var port;

      for (i = 0; i < 4096; i++) {
        port = this._rand(10000, 19999);
        if (this.usedPorts.indexOf(port) === -1) {
          break;
        }
      }

      return port;
    },
    _get_free_interface: function() {
      var i;
      var iface;

      for (i = 0; i < 64; i++) {
        iface = 'tun' + i;
        if (this.usedInterfaces.indexOf(iface) === -1) {
          break;
        }
      }

      return iface;
    }
  });

  return ModalAddServerView;
});
