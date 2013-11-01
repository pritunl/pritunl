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
          this.$('input').val(window.location.protocol + '//' +
            window.location.host + this.model.get('url'));
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger', 'Failed to generate key url.');
        }.bind(this)
      });
    },
    onClickInput: function() {
      this.$('input').select();
    }
  });

  return ModalKeyLinkView;
});
