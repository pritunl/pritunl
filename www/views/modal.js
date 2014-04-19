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
      'click .close, .cancel': 'dismiss',
      'click .ok': 'onOk',
      'hidden.bs.modal .modal': 'onRemove',
      'keyup input': 'onInputChange',
      'paste input': 'onInputChange',
      'input input': 'onInputChange',
      'propertychange input': 'onInputChange'
    },
    title: '',
    okText: 'Ok',
    cancelText: 'Cancel',
    safeClose: false,
    body: function() {
      return '';
    },
    initialize: function() {
      this.render();
      this.postRender();
    },
    deinitialize: function() {
      this.$('.modal').modal('hide');
      $('.modal-backdrop').remove();
    },
    render: function() {
      this.$el.html(this.modalTemplate({
        title: this.title,
        cancelText: this.cancelText,
        okText: this.okText
      }));
      this.$('.modal-body').append(this.body());
      this.$('.modal').modal({
        backdrop: this.safeClose ? 'static' : true,
        keyboard: this.safeClose ? false : true,
      });
      this.$('[data-toggle="tooltip"]').tooltip();
      $('body').append(this.el);
      if (this.inputMatch) {
        this.$('.ok').attr('disabled', 'disabled');
      }
      return this;
    },
    postRender: function() {
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
        if (type === 'info' || type === 'warning') {
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
    setLoading: function(message, noButtonDisable, timeout) {
      if (this.loading) {
        return;
      }
      this.loading = true;

      if (!noButtonDisable) {
        this.$('.ok').attr('disabled', 'disabled');
      }
      if (timeout === undefined) {
        timeout = 575;
      }

      if (this.loadingView) {
        if (this.loadingView.message !== message) {
          this.loadingView.close(function() {
            this.setLoading(message);
          }.bind(this));
          this.loadingView = null;
        }
        return;
      }

      setTimeout(function() {
        if (!this.loading) {
          return;
        }
        this.loading = false;
        this.loadingView = new AlertView({
          type: 'info',
          message: message
        });
        this.addView(this.loadingView);
        this.$('.modal-body').append(this.loadingView.render().el);
      }.bind(this), timeout);
    },
    clearLoading: function() {
      this.loading = false;
      if (this.loadingView) {
        this.loadingView.close();
        this.loadingView = null;
      }
      this.$('.ok').removeAttr('disabled');
    },
    dismiss: function() {
      if (this.safeClose && this.lockClose) {
        return;
      }
      this.clearAlert();
      this.clearLoading();
      this.$('.modal').modal('hide');
    },
    close: function(triggerApplied) {
      if (this.safeClose && this.lockClose) {
        return;
      }
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
    },
    onInputChange: function(evt) {
      if (!this.inputMatch) {
        return;
      }
      var matchText = this.inputMatchText;
      if (!matchText || matchText === $(evt.target).val()) {
        this.$('.ok').removeAttr('disabled');
      }
      else {
        this.$('.ok').attr('disabled', 'disabled');
      }
    }
  });

  return ModalView;
});
