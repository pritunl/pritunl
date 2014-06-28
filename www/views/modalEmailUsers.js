define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalEmailUsers.html'
], function($, _, Backbone, ModalView, AlertView, modalEmailUsersTemplate) {
  'use strict';
  var ModalEmailUsersView = ModalView.extend({
    className: 'email-users-modal',
    template: _.template(modalEmailUsersTemplate),
    title: 'Email Users',
    okText: 'Send',
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
      this.setLoading('Emailing users...');

      var i;
      var model;
      var users = this.collection.models.slice(0);
      var error = false;
      var count = users.length;
      var saveData = {
        success: function() {
          if (--count < 1 && !error) {
            this.close(true);
          }
        }.bind(this),
        error: function() {
          if (!error) {
            error = true;
            this.clearLoading();
            this.setAlert('danger',
              'Failed to email users, server error occurred.');
          }
        }.bind(this)
      };
      if (!count) {
        this.close();
      }
      for (i = 0; i < users.length; i++) {
        model = users[i].clone();
        model.save({
          send_key_email: true
        }, saveData);
      }
    }
  });

  return ModalEmailUsersView;
});
