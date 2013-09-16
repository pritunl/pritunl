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
    render: function() {
      this.$el.html(this.template());
      var searchView = new SearchView();
      this.$('.navbar-collapse').append(searchView.render().el);
      return this;
    }
  });

  return HeaderView;
});
