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
    body: function() {
      return '';
    },
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
      this.$('.modal-body').append(this.body());
      this.$('.modal').modal();
      this.$('[data-toggle="tooltip"]').tooltip();
      $('body').append(this.el);
      return this;
    },
    setAlert: function(type, message, form) {
      if (this.alertView) {
        if (this.alertView.type !== type ||
            this.alertView.message !== message) {
          this.alertView.close(function() {
            this.setAlert(type, message, form);
          }.bind(this));
          this.$('.form-group').removeClass('has-warning has-error');
          this.alertView = null;
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
      this.addView(this.alertView);
      this.$('.modal-body').prepend(this.alertView.render().el);
      if (form) {
        if (type === 'info') {
          this.$(form).addClass('has-warning');
        }
        else {
          this.$(form).addClass('has-error');
        }
      }
    },
    clearAlert: function() {
      if (this.alertView) {
        this.alertView.close();
        this.alertView = null;
        this.$('.form-group').removeClass('has-warning has-error');
      }
    },
    setLoading: function(message, noButtonDisable) {
      if (this.loadingView) {
        if (this.loadingView.message !== message) {
          this.loadingView.close(function() {
            this.setLoading(message);
          }.bind(this));
          this.loadingView = null;
        }
        return;
      }

      if (!noButtonDisable) {
        this.$('.ok').attr('disabled', 'disabled');
      }
      this.loadingView = new AlertView({
        type: 'info',
        message: message
      });
      this.addView(this.loadingView);
      this.$('.modal-body').append(this.loadingView.render().el);
    },
    clearLoading: function() {
      if (this.loadingView) {
        this.loadingView.close();
        this.loadingView = null;
      }
      this.$('.ok').removeAttr('disabled');
    },
    close: function(triggerApplied) {
      if (triggerApplied) {
        this.trigger('applied');
      }
      this.clearAlert();
      this.clearLoading();
      this.$('.modal').modal('hide');
    },
    onOk: function() {
      this.close();
    },
    onRemove: function() {
      this.destroy();
    }
  });

  return ModalView;
});
