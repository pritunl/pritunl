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
    events: function() {
      return {
        'click .ok': 'onOk',
        'hidden.bs.modal .modal': 'onRemove'
      }
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
      this.$('.modal-body').html(this.body());
      this.$('.modal').modal();
      this.$('[data-toggle="tooltip"]').tooltip();
      $('body').append(this.el);
      return this;
    },
    setAlert: function(type, message) {
      if (this.alertView) {
        if (this.alertView.type !== type ||
            this.alertView.message !== message) {
          this.alertView.close(function() {
            this.setAlert(type, message);
          }.bind(this));
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
      this.$('form').prepend(this.alertView.render().el);
    },
    clearAlert: function() {
      if (this.alertView) {
        this.alertView.close();
        this.alertView = null;
      }
    },
    setLoading: function(message) {
      if (this.loadingView) {
        if (this.loadingView.message !== message) {
          this.loadingView.close(function() {
            this.setLoading(message);
          }.bind(this));
          this.loadingView = null;
        }
        return;
      }

      this.loadingView = new AlertView({
        type: 'info',
        message: message
      });
      this.addView(this.loadingView);
      this.$('form').append(this.loadingView.render().el);
    },
    clearLoading: function() {
      if (this.loadingView) {
        this.loadingView.close();
        this.loadingView = null;
      }
    },
    close: function(triggerApplied) {
      this.applied = triggerApplied;
      this.clearAlert();
      this.clearLoading();
      this.$('.modal').modal('hide');
    },
    onOk: function() {
      this.close();
    },
    onRemove: function() {
      if (this.applied) {
        this.trigger('applied');
      }
      this.destroy();
    }
  });

  return ModalView;
});
