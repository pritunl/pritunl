define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalHostSettings.html'
], function($, _, Backbone, ModalView, modalHostSettingsTemplate) {
  'use strict';
  var ModalHostSettingsView = ModalView.extend({
    className: 'host-settings-modal',
    template: _.template(modalHostSettingsTemplate),
    title: 'Host Settings',
    okText: 'Save',
    hasAdvanced: true,
    body: function() {
      return this.template(this.model.toJSON());
    },
    onOk: function() {
      var name = this.$('.name input').val() || null;
      var publicAddress = this.$('.public-address input').val() || null;
      var linkAddress = this.$('.link-address input').val() || null;

      this.setLoading('Saving host...');
      this.model.save({
        name: name,
        public_address: publicAddress,
        link_address: linkAddress
      }, {
        success: function() {
          this.close(true);
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to modify host, server error occurred.');
        }.bind(this)
      });
    }
  });

  return ModalHostSettingsView;
});
