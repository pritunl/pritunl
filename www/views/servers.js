define([
  'jquery',
  'underscore',
  'backbone',
  'views/serversList',
  'text!templates/servers.html'
], function($, _, Backbone, ServersListView, serversTemplate) {
  'use strict';
  var ServersView = Backbone.View.extend({
    className: 'servers container',
    template: _.template(serversTemplate),
    initialize: function(options) {
      this.serversList = new ServersListView();
      this.addView(this.serversList);
    },
    render: function() {
      this.$el.html(this.template());
      this.$el.append(this.serversList.render().el);
      return this;
    }
  });

  return ServersView;
});
