define([
  'jquery',
  'underscore',
  'backbone',
  'models/server',
  'views/modal',
  'text!templates/modalAddServer.html'
], function($, _, Backbone, ServerModel, ModalView, modalAddServerTemplate) {
  'use strict';
  var ModalAddServerView = ModalView.extend({
    template: _.template(modalAddServerTemplate),
    title: 'Add Server',
    okText: 'Add',
    initialize: function() {
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
    onOk: function() {
      if (this.locked) {
        return;
      }
      var name = this.$('.name').val();
      var network = this.$('.network').val();
      var iface = this.$('.interface').val();
      var port = this.$('.port').val();
      var protocol = this.$('.protocol').val();

      if (!name) {
        this.setAlert('danger', 'Name can not be empty.');
        return;
      }
      if (!network) {
        this.setAlert('danger', 'Network can not be empty.');
        return;
      }
      if (!iface) {
        this.setAlert('danger', 'Interface can not be empty.');
        return;
      }
      if (!port) {
        this.setAlert('danger', 'Port can not be empty.');
        return;
      }
      this.locked = true;
      this.setLoading('Adding server...');
      this.model.save({
        name: name,
        network: network,
        interface: iface,
        port: port,
        protocol: protocol
      }, {
        success: function() {
          this.triggerEvt = true;
          this.close();
        }.bind(this),
        error: function(model, response) {
          this.clearLoading();
          if (response.responseJSON) {
            this.setAlert('danger', response.responseJSON.error_msg);
          }
          else {
            this.setAlert('danger',
              'Failed to add server, server error occurred.');
          }
          this.locked = false;
        }.bind(this)
      });
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
