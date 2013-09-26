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
        'click .selector': 'onSelect'
      });
    },
    body: function() {
      return this.template(this.model.toJSON());
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
      var publicAddress = this.$('.public-address select').val();

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
      if (!publicAddress) {
        this.setAlert('danger', 'Public IP can not be empty.');
        return;
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
        'public_address': publicAddress
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
