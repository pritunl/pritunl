define([
  'jquery',
  'underscore',
  'backbone',
  'bootstrap',
  'views/alert',
  'text!templates/modal.html'
], function($, _, Backbone, Bootstrap, AlertView, modalTemplate) {
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
      this.children = [];
      this.render();
    },
    deinitialize: function() {
      if (this.alertView) {
        this.children.push(this.alertView);
      }
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
    setAlert: function(type, message) {
      if (this.alertView) {
        if (this.alertView.type !== type ||
            this.alertView.message !== message) {
          this.alertView.close(function() {
            this.alertView = null;
            this.setAlert(type, message);
          }.bind(this));
        }
        else {
          this.alertView.flash();
        }
        return;
      }

      this.alertView = new AlertView({
        type: type,
        message: message
      });
      this.$('form').prepend(this.alertView.render().el);
    },
    clearAlert: function() {
      if (this.alertView) {
        this.alertView.close();
        this.alertView = null;
      }
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
