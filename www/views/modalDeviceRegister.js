define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalDeviceRegister.html'
], function($, _, Backbone, ModalView, modalDeviceRegister) {
  'use strict';
  var ModalDeviceRegister = ModalView.extend({
    className: 'device-register-modal',
    template: _.template(modalDeviceRegister),
    title: 'Register User Device',
    okText: 'Register',
    events: function() {
      return _.extend({
        'click input': 'onClickInput'
      }, ModalDeviceRegister.__super__.events);
    },
    initialize: function() {
      ModalDeviceRegister.__super__.initialize.call(this);
    },
    body: function() {
      return this.template();
    },
    onInputChange: function(evt) {
      $(evt.target).val(($(evt.target).val() || '').toUpperCase());
    },
    onOk: function() {
      var regKey = this.$('.reg-key input').val();

      if (!regKey) {
        this.setAlert('danger', 'Missing registration key.', '.reg-key');
        return;
      }

      this.setLoading('Registering device...');
      this.model.save({
        reg_key: regKey,
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

  return ModalDeviceRegister;
});
