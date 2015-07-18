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
      'click .close': 'onClose'
    },
    initialize: function(options) {
      this.type = options.type;
      this.message = options.message;
      this.dismissable = options.dismissable;
      this.animate = options.animate === false ? false : true;
      this.force = options.force;
      this.render();
    },
    render: function() {
      if (!this.force && !window.authenticated) {
        this.destroy();
        return this;
      }
      this.$el.html(this.template({
        type: this.type,
        message: this.message,
        dismissable: this.dismissable
      }));
      if (this.animate) {
        this.$el.hide();
        this.$el.slideDown(window.slideTime);
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
          }.bind(this), 150);
        }.bind(this), 150);
      }.bind(this), 150);
    },
    onClose: function() {
      this.close();
    },
    close: function(complete) {
      this.$el.slideUp(window.slideTime, function() {
        this.destroy();
        if (complete) {
          complete();
        }
      }.bind(this));
    }
  });

  return AlertView;
});
