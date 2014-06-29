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
      var i;
      var alertView;
      var removingOnlineUsers = false;
      var removingServerUsers = false;
      ModalDeleteUsersView.__super__.initialize.call(this);
      for (i = 0; i < this.collection.models.length; i++) {
        if (this.collection.models[i].get('status')) {
          removingOnlineUsers = true;
        }
        if (this.collection.models[i].get('type') === 'server') {
          removingServerUsers = true;
        }
      }
      if (removingOnlineUsers) {
        alertView = new AlertView({
          type: 'danger',
          message: 'Deleting online users will restart the servers ' +
           'that the users are connected to.',
          animate: false
        });
        this.addView(alertView);
        this.$('.modal-body').prepend(alertView.render().el);
      }
      if (removingServerUsers) {
        alertView = new AlertView({
          type: 'danger',
          message: 'Warning, deleting server users can break the servers.',
          animate: false
        });
        this.addView(alertView);
        this.$('.modal-body').prepend(alertView.render().el);
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
      var model;
      var users = this.collection.models.slice(0);
      var error = false;
      var count = users.length;
      var destroyData = {
        success: function() {
          if (--count < 1 && !error) {
            this.close(true);
          }
        }.bind(this),
        error: function() {
          if (!error) {
            this.$('.ok').hide();
            this.$('.cancel').text('Close');
            error = true;
            this.clearLoading();
            this.setAlert('danger',
              'Failed to delete users, server error occurred.');
          }
        }.bind(this)
      };
      if (!count) {
        this.close();
      }
      for (i = 0; i < users.length; i++) {
        model = users[i].clone();
        model.destroy(destroyData);
      }
    }
  });

  return ModalDeleteUsersView;
});
