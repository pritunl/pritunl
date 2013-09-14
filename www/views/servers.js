define([
  'jquery',
  'underscore',
  'backbone',
  'text!templates/servers.html'
], function($, _, Backbone, serversTemplate) {
  'use strict';
  var ServersView = Backbone.View.extend({
    template: _.template(serversTemplate),
    render: function() {
      this.$el.html(this.template());
      return this;
    }
  });

  return ServersView;
});
