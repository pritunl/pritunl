define([
  'jquery',
  'underscore',
  'backbone',
  'bootstrap',
  'text!templates/modal.html'
], function($, _, Backbone, Bootstrap, modalTemplate) {
  'use strict';
  var ModalView = Backbone.View.extend({
    template: _.template(modalTemplate),
    events: {
      'click .close': 'onRemove'
    },
    initialize: function(options) {
      this.title = options.title;
      this.body = options.body;
      this.cancelText = options.cancelText || 'Cancel';
      this.okText = options.okText || 'Ok';
      this.render();
    },
    render: function() {
      this.$el.html(this.template({
        title: this.title,
        body: this.body,
        cancelText: this.cancelText,
        okText: this.okText
      }));
      this.$('.modal').modal();
      $('body').append(this.el);
      return this;
    },
    onRemove: function() {
      this.$el.slideUp(250, function() {
        this.remove();
      });
    }
  });

  return ModalView;
});
