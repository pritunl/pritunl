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
      this.$('.server-uptime .status-text').text(
        this.model.get('uptime'));
      this.$('.server-users .status-num').text(
        this.model.get('users_online') + '/' + this.model.get('users_total'));
      this.$('.server-network .status-text').text(
        this.model.get('network'));
      this.$('.server-interface .status-text').text(
        this.model.get('interface'));
      this.$('.server-port .status-text').text(
        this.model.get('port'));

      if (this.model.get('status') === 'online') {
        this.$('.server-start').hide();
        this.$('.server-stop').show();
        this.$('.server-restart').removeAttr('disabled');
      }
      else {
        this.$('.server-stop').hide();
        this.$('.server-start').show();
        this.$('.server-restart').attr('disabled', 'disabled');
      }
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      this.update();
      this.$el.append(this.serverOrgsListView.render().el);
      return this;
    }
  });

  return ServersListItemView;
});
