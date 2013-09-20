define([
  'jquery',
  'underscore',
  'backbone',
  'text!templates/serversListItem.html'
], function($, _, Backbone, serversListItemTemplate) {
  'use strict';
  var ServersListItemView = Backbone.View.extend({
    className: 'server',
    template: _.template(serversListItemTemplate),
    update: function() {
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    }
  });

  return ServersListItemView;
});
