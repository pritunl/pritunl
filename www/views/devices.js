define([
  'jquery',
  'underscore',
  'backbone',
  'views/devicesList'
], function($, _, Backbone, DevicesListView) {
  'use strict';
  var DevicesView = Backbone.View.extend({
    className: 'devices container',
    initialize: function() {
      this.devicesList = new DevicesListView();
      this.addView(this.devicesList);
    },
    render: function() {
      this.$el.append(this.devicesList.render().el);
      return this;
    }
  });

  return DevicesView;
});
