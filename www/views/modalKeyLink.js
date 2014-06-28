define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalKeyLink.html'
], function($, _, Backbone, ModalView, modalKeyLinkTemplate) {
  'use strict';
  var ModalKeyLinkView = ModalView.extend({
    className: 'key-link-modal',
    template: _.template(modalKeyLinkTemplate),
    title: 'Temporary Key Link',
    cancelText: null,
    okText: 'Close',
    events: function() {
      return _.extend({
        'click input': 'onClickInput'
      }, ModalKeyLinkView.__super__.events);
    },
    body: function() {
      return this.template();
    },
    postRender: function() {
      this.setLoading('Generating url...', true);
      this.model.fetch({
        success: function() {
          this.clearLoading();
          var keyLink = window.location.protocol + '//' +
            window.location.host + this.model.get('key_url');
          var otpLink = window.location.protocol + '//' +
            window.location.host + this.model.get('view_url');
          var uriProtocol;
          if (window.location.protocol.replace(':', '') === 'http') {
            uriProtocol = 'pt';
          }
          else {
            uriProtocol = 'pts';
          }
          var uriLink = uriProtocol + '://' +
            window.location.host + this.model.get('uri_url');

          this.$('.key-link input').val(keyLink);
          this.$('.key-link a').attr('href', keyLink);
          this.$('.otp-link input').val(otpLink);
          this.$('.otp-link a').attr('href', otpLink);
          this.$('.uri-link input').val(uriLink);
          this.$('.uri-link a').attr('href', uriLink);
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger', 'Failed to generate key url.');
        }.bind(this)
      });
    },
    onClickInput: function(evt) {
      this.$(evt.target).select();
    }
  });

  return ModalKeyLinkView;
});
