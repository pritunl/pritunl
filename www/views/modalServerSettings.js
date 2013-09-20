define([
  'jquery',
  'underscore',
  'backbone',
  'models/server',
  'views/modal',
  'text!templates/modalAddServer.html'
], function($, _, Backbone, ServerModel, ModalView, modalAddServerTemplate) {
  'use strict';
  var ModalServerSettingsView = ModalView.extend({
    template: _.template(modalAddServerTemplate),
    title: 'Server Settings',
    okText: 'Save',
    initialize: function(options) {
      this.body = this.template(this.model.toJSON());
      this.render();
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
      this.setLoading('Saving server...');
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
      this.trigger('saved');
    }
  });

  return ModalServerSettingsView;
});
