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
      'click .close': 'onRemove'
    },
    initialize: function(options) {
      this.type = options.type;
      this.message = options.message;
      this.render();
    },
    render: function() {
      this.$el.html(this.template({
        type: this.type,
        message: this.message
      }));
      this.$el.hide();
      $('.alerts-container').append(this.el);
      this.$el.slideDown(250);
      return this;
    },
    onRemove: function() {
      this.$el.slideUp(250, function() {
        this.remove();
      });
    }
  });

  return AlertView;
});
