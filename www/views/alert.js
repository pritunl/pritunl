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
      this.render();
    },
    render: function() {
      this.$el.html(this.template({
        type: this.type,
        message: this.message,
        dismissable: this.dismissable
      }));
      this.$el.hide();
      this.$el.slideDown(250);
      return this;
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
