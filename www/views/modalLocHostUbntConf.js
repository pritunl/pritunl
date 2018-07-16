define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalLocHostConf.html'
], function($, _, Backbone, ModalView, modalLocHostConfTemplate) {
  'use strict';
  var ModalLocHostUbntConfView = ModalView.extend({
    className: 'location-host-conf-modal',
    template: _.template(modalLocHostConfTemplate),
    title: 'Location Host EdgeRouter Configuration',
    cancelText: null,
    okText: 'Close',
    initialize: function() {
      ModalLocHostUbntConfView.__super__.initialize.call(this);
      this.setAlert('danger', 'Static host configuration is not valid ' +
        'when locations contain more then one host or all locations do ' +
        'not yet have an active host. Only one route per location is ' +
        'supported with the Edgerouter.');
    },
    body: function() {
      return this.template();
    },
    postRender: function() {
      this.setLoading('Getting location host static configuration...', true);
      this.model.set({
        'hostname': window.location.host
      });
      this.model.fetch({
        success: function() {
          this.clearLoading();
          this.$('.conf-link textarea').val(this.model.get('ubnt_conf'));
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

  return ModalLocHostUbntConfView;
});
