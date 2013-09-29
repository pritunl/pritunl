define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalDeleteUsers.html'
], function($, _, Backbone, ModalView, AlertView, modalDeleteUsersTemplate) {
  'use strict';
  var ModalDeleteUsersView = ModalView.extend({
    className: 'delete-users-modal',
    template: _.template(modalDeleteUsersTemplate),
    title: 'Delete Users',
    okText: 'Delete',
    initialize: function() {
      ModalDeleteUsersView.__super__.initialize.call(this);
      var i;
      for (i = 0; i < this.collection.models.length; i++) {
        if (this.collection.models[i].get('type') !== 'server') {
          continue;
        }
        var alertView = new AlertView({
          type: 'danger',
          message: 'Warning, deleting server users can break the servers.',
          animate: false
        });
        this.addView(alertView);
        this.$('form').prepend(alertView.render().el);
        break;
      }
    },
    body: function() {
      var i;
      var nameId;
      var users = [];
      var usersSort = [];
      var usersObj = {};
      var usersData = this.collection.toJSON();

      for (i = 0; i < usersData.length; i++) {
        nameId = usersData[i].name + '_' + usersData[i].id;
        usersSort.push(nameId);
        usersObj[nameId] = usersData[i];
      }
      usersSort.sort();
      for (i = 0; i < usersSort.length; i++) {
        users.push(usersObj[usersSort[i]]);
      }

      return this.template({
        users: users
      });
    },
    onOk: function() {
      this.setLoading('Deleting users...');

      var i;
      var users = this.collection.models.slice(0);
      var count = users.length;
      var destroyData = {
        success: function() {
          if (--count < 1) {
            this.close(true);
          }
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to delete users, server error occurred.');
        }.bind(this)
      };
      for (i = 0; i < users.length; i++) {
        users[i].destroy(destroyData);
      }
    }
  });

  return ModalDeleteUsersView;
});
