define([
  'jquery',
  'underscore',
  'backbone',
  'text!templates/search.html'
], function($, _, Backbone, searchTemplate) {
  'use strict';
  var SearchView = Backbone.View.extend({
    template: _.template(searchTemplate),
    render: function() {
      this.$el.html(this.template());
      return this;
    }
  });

  return SearchView;
});
