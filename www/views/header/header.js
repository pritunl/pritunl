define([
  'jquery',
  'underscore',
  'backbone',
  'text!templates/header/header.html'
], function($, _, Backbone, headerTemplate) {
  'use strict';
  var HeaderView = Backbone.View.extend({
    tagName: 'header',
    template: _.template(headerTemplate),
    render: function() {
      this.$el.html(this.template());
      return this;
    }
  });

  return HeaderView;
});
