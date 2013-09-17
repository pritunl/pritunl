define([
  'jquery',
  'underscore',
  'backbone',
  'views/search',
  'text!templates/header.html'
], function($, _, Backbone, SearchView, headerTemplate) {
  'use strict';
  var HeaderView = Backbone.View.extend({
    tagName: 'header',
    template: _.template(headerTemplate),
    initialize: function() {
      this.children = [];
      this.searchView = new SearchView();
      this.children.push(this.searchView);
    },
    render: function() {
      this.$el.html(this.template());
      this.$('.navbar-collapse').append(this.searchView.render().el);
      return this;
    }
  });

  return HeaderView;
});
