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
    title: 'Temporary Profile Link',
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
      this.setLoading('Generating temporary url...', true);
      this.model.fetch({
        success: function() {
          this.clearLoading();
          var keyLink = window.location.protocol + '//' +
            window.location.host + this.model.get('key_url');
          var keyZipLink = window.location.protocol + '//' +
            window.location.host + this.model.get('key_zip_url');
          var keyOncLink = window.location.protocol + '//' +
            window.location.host + this.model.get('key_onc_url');
          var otpLink = window.location.protocol + '//' +
            window.location.host + this.model.get('view_url');
          var uriLink = 'pritunl://' + window.location.host +
            this.model.get('uri_url');

          this.$('.key-link input').val(keyLink);
          this.$('.key-link a').attr('href', keyLink);
          this.$('.key-zip-link input').val(keyZipLink);
          this.$('.key-zip-link a').attr('href', keyZipLink);
          this.$('.key-onc-link input').val(keyOncLink);
          this.$('.key-onc-link a').attr('href', keyOncLink);
          this.$('.otp-link input').val(otpLink);
          this.$('.otp-link a').attr('href', otpLink);
          this.$('.uri-link input').val(uriLink);
          this.$('.uri-link a').attr('href', uriLink);
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
    },
    onClickInput: function(evt) {
      this.$(evt.target).select();
    }
  });

  return ModalKeyLinkView;
});
