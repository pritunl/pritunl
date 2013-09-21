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
    template: _.template(modalDeleteUsersTemplate),
    title: 'Delete Users',
    okText: 'Delete',
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
      if (this.locked) {
        return;
      }
      this.locked = true;
      this.setLoading('Deleting users...');

      var i;
      var users = this.collection.models.slice(0);
      var count = users.length;
      for (i = 0; i < users.length; i++) {
        users[i].destroy({
          success: function() {
            count -= 1;
            if (count === 0) {
              this.close(true);
            }
          }.bind(this),
          error: function() {
            this.clearLoading();
            this.setAlert('danger',
              'Failed to delete users, server error occurred.');
            this.locked = false;
          }.bind(this)
        });
      }
    }
  });

  return ModalDeleteUsersView;
});
