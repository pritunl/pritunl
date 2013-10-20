define([
  'jquery',
  'underscore',
  'backbone',
  'text!templates/dashboardLogItem.html'
], function($, _, Backbone, dashboardLogItemTemplate) {
  'use strict';
  var DashboardLogItemView = Backbone.View.extend({
    className: 'log-entry clearfix',
    template: _.template(dashboardLogItemTemplate),
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    },
    update: function() {
      this.$('.log-msg').text(this.model.get('message'));
      this.$('.log-time').text(window.formatTime(this.model.get('time')));
    }
  });

  return DashboardLogItemView;
});
