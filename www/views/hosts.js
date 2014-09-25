define([
  'jquery',
  'underscore',
  'backbone',
  'views/hostsList'
], function($, _, Backbone, HostsListView) {
  'use strict';
  var HostsView = Backbone.View.extend({
    className: 'hosts container',
    initialize: function() {
      this.hostsList = new HostsListView();
      this.addView(this.hostsList);
    },
    render: function() {
      this.$el.append(this.hostsList.render().el);
      return this;
    }
  });

  return HostsView;
});
