define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalLocHostConf.html'
], function($, _, Backbone, ModalView, modalLocHostConfTemplate) {
  'use strict';
  var ModalLocHostConfView = ModalView.extend({
    className: 'location-host-conf-modal',
    template: _.template(modalLocHostConfTemplate),
    title: 'Location Host Static Configuration',
    cancelText: null,
    okText: 'Close',
    initialize: function() {
      ModalLocHostConfView.__super__.initialize.call(this);
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
          this.$('.conf-link textarea').val(this.model.get('conf'));
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

  return ModalLocHostConfView;
});
