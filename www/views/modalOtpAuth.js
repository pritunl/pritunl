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
      this.$('input').val(this.model.get('otp_secret'));
      var otpUrl = 'otpauth://totp/' + this.model.get('name') + '@' +
        'pritunl' + '?secret=' + this.model.get('otp_secret');
      new QRCode(this.$('.qrcode').get(0), {
          text: otpUrl,
          width: 192,
          height: 192,
          colorDark : '#10206e',
          colorLight : '#fff'
      });
    },
    onGenerateNewKey: function() {
      this.$('.generate-new-key').attr('disabled', 'disabled');
      this.setLoading('Generating new key...');
      this.model.destroyOtpSecret({
        success: function() {
          this.close(true);
        }.bind(this),
        error: function() {
          this.$('.generate-new-key').removeAttr('disabled');
          this.clearLoading();
          this.setAlert('danger',
            'Failed to generate new key, server error occurred.');
        }.bind(this)
      });
    },
    onClickInput: function() {
      this.$('input').select();
    }
  });

  return ModalOtpAuthView;
});
