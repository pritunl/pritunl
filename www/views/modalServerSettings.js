define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalServerSettings.html'
], function($, _, Backbone, ModalView, modalServerSettingsTemplate) {
  'use strict';
  var ModalServerSettingsView = ModalView.extend({
    className: 'server-settings-modal',
    template: _.template(modalServerSettingsTemplate),
    title: 'Server Settings',
    okText: 'Save',
    loadingMsg: 'Saving server...',
    errorMsg: 'Failed to saving server, server error occurred.',
    events: function() {
      return _.extend(ModalServerSettingsView.__super__.events, {
        'click .local-network-toggle .selector': 'onLocalNetworkSelect',
        'click .debug-toggle .selector': 'onDebugSelect'
      });
    },
    body: function() {
      return this.template(this.model.toJSON());
    },
    getLocalNetworkSelect: function() {
      return this.$('.local-network-toggle .selector').hasClass('selected');
    },
    setLocalNetworkSelect: function(state) {
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
    onLocalNetworkSelect: function() {
      this.setLocalNetworkSelect(!this.getLocalNetworkSelect());
    },
    getDebugSelect: function() {
      return this.$('.debug-toggle .selector').hasClass('selected');
    },
    setDebugSelect: function(state) {
      if (state) {
        this.$('.debug-toggle .selector').addClass('selected');
        this.$('.debug-toggle .selector-inner').show();
      }
      else {
        this.$('.debug-toggle .selector').removeClass('selected');
        this.$('.debug-toggle .selector-inner').hide();
      }
      this.trigger('select', this);
    },
    onDebugSelect: function() {
      this.setDebugSelect(!this.getDebugSelect());
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
      var publicAddress = this.$('.public-address input').val();
      var localNetwork = null;
      var debug = this.getDebugSelect();

      if (!name) {
        this.setAlert('danger', 'Name can not be empty.', '.name');
        return;
      }
      if (!network) {
        this.setAlert('danger', 'Network can not be empty.', '.network');
        return;
      }
      if (!iface) {
        this.setAlert('danger', 'Interface can not be empty.', '.interface');
        return;
      }
      if (!port) {
        this.setAlert('danger', 'Port can not be empty.', '.port');
        return;
      }
      if (!publicAddress) {
        this.setAlert('danger', 'Public IP can not be empty.',
          '.public-address');
        return;
      }
      if (this.getLocalNetworkSelect()) {
        localNetwork = this.$('.local-network input').val();
        if (!localNetwork) {
          this.setAlert('danger', 'Local network can not be empty.',
            '.local-network');
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
        'local_network': localNetwork,
        'public_address': publicAddress,
        'debug': debug
      }, {
        success: function() {
          this.close(true);
        }.bind(this),
        error: function(model, response) {
          this.clearLoading();
          if (response.responseJSON) {
            this.setAlert('danger', response.responseJSON.error_msg);
          }
          else {
            this.setAlert('danger', this.errorMsg);
          }
          this.locked = false;
        }.bind(this)
      });
    }
  });

  return ModalServerSettingsView;
});
