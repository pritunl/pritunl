define([
  'jquery',
  'underscore',
  'backbone',
  'text!templates/alert.html'
], function($, _, Backbone, alertTemplate) {
  'use strict';
  var AlertView = Backbone.View.extend({
    template: _.template(alertTemplate),
    events: {
      'click .close': 'close'
    },
    initialize: function(options) {
      this.type = options.type;
      this.message = options.message;
      this.dismissable = options.dismissable;
      this.animate = options.animate || true;
      this.render();
    },
    render: function() {
      this.$el.html(this.template({
        type: this.type,
        message: this.message,
        dismissable: this.dismissable
      }));
      if (this.animate) {
        this.$el.hide();
        this.$el.slideDown(250);
      }
      return this;
    },
    flash: function(complete) {
      this.$('.alert').addClass('flash');
      setTimeout(function() {
        this.$('.alert').removeClass('flash');
        setTimeout(function() {
          this.$('.alert').addClass('flash');
          setTimeout(function() {
            this.$('.alert').removeClass('flash');
            if (complete) {
              complete();
            }
          }.bind(this), 175);
        }.bind(this), 175);
      }.bind(this), 175);
    },
    close: function(complete) {
      this.$el.slideUp(250, function() {
        this.remove();
        if (complete) {
          complete();
        }
      });
    }
  });

  return AlertView;
});
