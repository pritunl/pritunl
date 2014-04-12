define([
  'jquery',
  'underscore',
  'backbone',,
  'text!templates/userServersListItem.html'
], function($, _, Backbone, userServersListItemTemplate) {
  'use strict';
  var UserServersListItemView = Backbone.View.extend({
    className: 'user-server',
    template: _.template(userServersListItemTemplate),
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    },
    update: function() {
      this.$('.server-name').text(this.model.get('name'));
      if (this.model.get('status')) {
        if (!this.$('.status-icon').hasClass('online')) {
          this.$('.status-icon').removeClass('offline');
          this.$('.status-icon').addClass('online');
          this.$('.status-text').text('Online');
        }
      }
      else {
        if (!this.$('.status-icon').hasClass('offline')) {
          this.$('.status-icon').removeClass('online');
          this.$('.status-icon').addClass('offline');
          this.$('.status-text').text('Offline');
        }
      }
    }
  });

  return UserServersListItemView;
});
