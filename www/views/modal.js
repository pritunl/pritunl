define([
  'jquery',
  'underscore',
  'backbone',
  'bootstrap',
  'text!templates/modal.html'
], function($, _, Backbone, Bootstrap, modalTemplate) {
  'use strict';
  var ModalView = Backbone.View.extend({
    modalTemplate: _.template(modalTemplate),
    events: {
      'click .ok': 'onOk',
      'hidden.bs.modal .modal': 'onRemove'
    },
    title: '',
    cancelText: 'Cancel',
    body: '',
    okText: 'Ok',
    initialize: function() {
      this.render();
    },
    render: function() {
      this.$el.html(this.modalTemplate({
        title: this.title,
        cancelText: this.cancelText,
        okText: this.okText
      }));
      this.$('.modal-body').html(this.body);
      this.$('.modal').modal();
      $('body').append(this.el);
      return this;
    },
    close: function() {
      this.$('.modal').modal('hide');
    },
    onOk: function() {
      this.close();
    },
    onRemove: function() {
      this.remove();
    }
  });

  return ModalView;
});
