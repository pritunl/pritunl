define([
  'jquery',
  'underscore',
  'backbone',
  'text!templates/search.html'
], function($, _, Backbone, searchTemplate) {
  'use strict';
  var SearchView = Backbone.View.extend({
    template: _.template(searchTemplate),
    events: {
      'keydown .search input': 'onSearch',
      'paste .search input': 'onSearch',
      'input .search input': 'onSearch',
      'propertychange .search input': 'onSearch'
    },
    render: function() {
      this.$el.html(this.template());
      return this;
    },
    onSearch: function() {
    }
  });

  return SearchView;
});
