define([
  'jquery',
  'underscore',
  'backbone',
  'views/linksList'
], function($, _, Backbone, LinksListView) {
  'use strict';
  var LinksView = Backbone.View.extend({
    className: 'links container',
    initialize: function() {
      this.linksList = new LinksListView();
      this.addView(this.linksList);
    },
    render: function() {
      this.$el.append(this.linksList.render().el);
      return this;
    }
  });

  return LinksView;
});
