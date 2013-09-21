define([
  'jquery',
  'underscore',
  'backbone',
  'models/server',
  'views/modal',
  'text!templates/modalServerSettings.html'
], function($, _, Backbone, ServerModel, ModalView,
    modalServerSettingsTemplate) {
  'use strict';
  var ModalServerSettingsView = ModalView.extend({
    className: 'server-settings-modal',
    template: _.template(modalServerSettingsTemplate),
    title: 'Server Settings',
    okText: 'Save',
    loadingMsg: 'Saving server...',
    errorMsg: 'Failed to saving server, server error occurred.',
    initialize: function() {
      // TODO
      this.events['click .selector'] = 'onSelect';
      this.body = this.template(this.model.toJSON());
      this.render();
    },
    getSelect: function() {
      return this.$('.local-network-toggle .selector').hasClass('selected');
    },
    setSelect: function(state) {
      if (state) {
        this.$('.local-network-toggle .selector').addClass('selected');
        this.$('.local-network-toggle .selector-inner').show();
        this.$('.local-network').slideDown(250);
      }
      else {
        this.$('.local-network-toggle .selector').removeClass('selected');
        this.$('.local-network-toggle .selector-inner').hide();
        this.$('.local-network').slideUp(250);
      }
      this.trigger('select', this);
    },
    onSelect: function() {
      this.setSelect(!this.getSelect());
    },
    onOk: function() {
      if (this.locked) {
        return;
      }
      var name = this.$('.name input').val();
      var network = this.$('.network input').val();
      var iface = this.$('.interface input').val();
      var port = this.$('.port input').val();
      var protocol = this.$('.protocol select').val();
      var localNetwork = null;

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
      if (this.getSelect()) {
        localNetwork = this.$('.local-network input').val();
        if (!localNetwork) {
          this.setAlert('danger', 'Local network can not be empty.');
          return;
        }
      }
      this.locked = true;
      this.setLoading(this.loadingMsg);
      this.model.save({
        'name': name,
        'network': network,
        'interface': iface,
        'port': port,
        'protocol': protocol,
        'local_network': localNetwork
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
            this.setAlert('danger', this.loadingMsg);
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
