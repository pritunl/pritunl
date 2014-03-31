define([
  'jquery',
  'underscore',
  'backbone',
  'qrcode',
  'views/modal',
  'text!templates/modalOtpAuth.html'
], function($, _, Backbone, QRCode, ModalView, modalOtpAuthTemplate) {
  'use strict';
  var ModalOtpAuthView = ModalView.extend({
    className: 'otp-auth-modal',
    template: _.template(modalOtpAuthTemplate),
    title: 'Two-Step Authentication Key',
    cancelText: null,
    okText: 'Close',
    events: function() {
      return _.extend({
        'click .generate-new-key': 'onGenerateNewKey',
        'click input': 'onClickInput'
      }, ModalOtpAuthView.__super__.events);
    },
    body: function() {
      return this.template();
    },
    postRender: function() {
      this.update();
      this.listenTo(this.model, 'change', this.update);
    },
    update: function(model) {
      // Only event from model will have model argument
      if (model) {
        this.$('.generate-new-key').removeAttr('disabled');
        this.clearLoading();
        this.setAlert('warning', 'Successfully generated new key.');
      }
      this.$('input').val(this.model.get('otp_secret'));
      var otpUrl = 'otpauth://totp/' + this.model.get('name') +
        '@' + this.model.get('organization_name') + '?secret=' +
        this.model.get('otp_secret');
      this.$('.qrcode').empty();
      new QRCode(this.$('.qrcode').get(0), {
          text: otpUrl,
          width: 192,
          height: 192,
          colorDark : '#3276b1',
          colorLight : '#fff'
      });
    },
    onGenerateNewKey: function() {
      this.$('.generate-new-key').attr('disabled', 'disabled');
      this.setLoading('Generating new key...');
      this.model.destroyOtpSecret({
        error: function() {
          this.$('.generate-new-key').removeAttr('disabled');
          this.clearLoading();
          this.setAlert('danger',
            'Failed to generate new key, server error occurred.');
        }.bind(this)
      });
    },
    onClickInput: function(evt) {
      this.$(evt.target).select();
    }
  });

  return ModalOtpAuthView;
});
