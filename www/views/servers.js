define([
  'jquery',
  'underscore',
  'backbone',
  'views/serversList'
], function($, _, Backbone, ServersListView) {
  'use strict';
  var ServersView = Backbone.View.extend({
    className: 'servers container',
    initialize: function() {
      this.serversList = new ServersListView();
      this.addView(this.serversList);
    },
    render: function() {
      this.$el.append(this.serversList.render().el);
      return this;
    }
  });

  return ServersView;
});
