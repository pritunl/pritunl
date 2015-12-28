define([
  'jquery',
  'underscore',
  'backbone',
  'views/adminsList',
  'text!templates/admins.html'
], function($, _, Backbone, AdminsListView, adminsTemplate) {
  'use strict';
  var AdminsView = Backbone.View.extend({
    template: _.template(adminsTemplate),
    className: 'admins container',
    events: {
      'click .admins-add-admin': 'onAddAdmin',
      'click .admins-del-selected': 'onDelSelected'
    },
    initialize: function() {
      this.adminsList = new AdminsListView();
      this.addView(this.adminsList);
    },
    render: function() {
      this.$el.html(this.template());
      this.$('.admins-container').append(this.adminsList.render().el);
      return this;
    }
  });

  return AdminsView;
});
