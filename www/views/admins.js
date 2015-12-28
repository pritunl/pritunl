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
      this.listenTo(this.adminsList, 'select', this.onSelect);
      this.addView(this.adminsList);
      this.selected = [];
    },
    onSelect: function(view) {
      var i;

      if (view.getSelect()) {
        this.selected.push(view);
      }
      else {
        for (i = 0; i < this.selected.length; i++) {
          if (this.selected[i] === view) {
            this.selected.splice(i, 1);
          }
        }
      }

      if (this.selected.length) {
        this.$('.admins-del-selected').removeAttr('disabled');
      }
      else {
        this.$('.admins-del-selected').attr('disabled', 'disabled');
      }
    },
    render: function() {
      this.$el.html(this.template());
      this.$('.admins-container').append(this.adminsList.render().el);
      return this;
    }
  });

  return AdminsView;
});
