define([
  'jquery',
  'underscore',
  'backbone',
  'collections/admin',
  'views/alert',
  'views/adminsList',
  'views/modalAddAdmin',
  'views/modalDeleteAdmins',
  'text!templates/admins.html'
], function($, _, Backbone, AdminCollection, AlertView, AdminsListView,
    ModalAddAdminView, ModalDeleteAdminsView, adminsTemplate) {
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
    onAddAdmin: function() {
      var modal = new ModalAddAdminView();
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully added administrator.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    onDelSelected: function() {
      var i;
      var models = [];

      for (i = 0; i < this.selected.length; i++) {
        models.push(this.selected[i].model);
      }

      var modal = new ModalDeleteAdminsView({
        collection: new AdminCollection(models)
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully deleted selected administrators.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    render: function() {
      this.$el.html(this.template());
      this.$('.admins-container').append(this.adminsList.render().el);
      return this;
    }
  });

  return AdminsView;
});
