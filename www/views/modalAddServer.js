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
    safeClose: true,
    initialize: function(options) {
      this.usedNetworks = options.usedNetworks;
      this.usedPorts = options.usedPorts;
      this.usedInterfaces = options.usedInterfaces;
      this.newServer = true;

      this.model = new ServerModel({
        'name': '',
        'network': this._get_free_network(),
        'port': this._get_free_port(),
        'protocol': 'udp',
        'dh_param_bits': 2048,
        'ipv6_firewall': true,
        'dns_servers': ['8.8.8.8'],
        'cipher': 'aes128',
        'hash': 'sha1',
        'inter_client': true,
        'restrict_routes': true,
        'vxlan': true
      });
      ModalAddServerView.__super__.initialize.call(this, options);
    },
    _rand: function(min, max) {
      return Math.floor(Math.random() * (max - min + 1)) + min;
    },
    _get_free_network: function() {
      var i;
      var network;

      for (i = 0; i < 64; i++) {
        network = '192.168.' + this._rand(215, 250) + '.0/24';
        if (this.usedNetworks.indexOf(network) === -1) {
          break;
        }
      }
      if (this.usedNetworks.indexOf(network) !== -1) {
        for (i = 0; i < 512; i++) {
          network = '192.168.' + this._rand(15, 215) + '.0/24';
          if (this.usedNetworks.indexOf(network) === -1) {
            break;
          }
        }
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
    }
  });

  return ModalAddServerView;
});
