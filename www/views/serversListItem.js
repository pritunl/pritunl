define([
  'jquery',
  'underscore',
  'backbone',
  'views/serverOrgsList',
  'text!templates/serversListItem.html'
], function($, _, Backbone, ServerOrgsListView, serversListItemTemplate) {
  'use strict';
  var ServersListItemView = Backbone.View.extend({
    className: 'server',
    template: _.template(serversListItemTemplate),
    initialize: function() {
      this.serverOrgsListView = new ServerOrgsListView({
        server: this.model.get('id')
      });
      this.addView(this.serverOrgsListView);
    },
    update: function() {
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      this.$el.append(this.serverOrgsListView.render().el);
      return this;
    }
  });

  return ServersListItemView;
});
