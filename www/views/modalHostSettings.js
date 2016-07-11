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
      var publicAddress6 = this.$('.public-address6 input').val() || null;
      var routedSubnet6 = this.$('.routed-subnet6 input').val() || null;
      var localAddress = this.$('.local-address input').val() || null;
      var localAddress6 = this.$('.local-address6 input').val() || null;
      var linkAddress = this.$('.link-address input').val() || null;
      var availabilityGroup = this.$('.availability-group input').val() || null;
      var instanceId = this.$('.instance-id input').val() || null;

      this.setLoading('Saving host...');
      this.model.save({
        name: name,
        public_address: publicAddress,
        public_address6: publicAddress6,
        routed_subnet6: routedSubnet6,
        local_address: localAddress,
        local_address6: localAddress6,
        link_address: linkAddress,
        availability_group: availabilityGroup,
        instance_id: instanceId
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
        }.bind(this)
      });
    }
  });

  return ModalHostSettingsView;
});
