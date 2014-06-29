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
    initialize: function() {
      var i;
      ModalEmailUsersView.__super__.initialize.call(this);
      for (i = 0; i < this.collection.models.length; i++) {
        if (!this.collection.models[i].get('email')) {
          var alertView = new AlertView({
            type: 'warning',
            message: 'Warning, not all of selected users have an email ' +
              'address configured and will not receive a key email.',
            animate: false
          });
          this.addView(alertView);
          this.$('.modal-body').prepend(alertView.render().el);
          break;
        }
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
    setUserText: function(model, color, text) {
      var email = model.get('email');
      this.$('.user-' + model.get('id')).removeClass(
        'primary-text-light error-text-light warning-text-light ' +
        'success-text-light');
      this.$('.user-' + model.get('id')).addClass(color);
      this.$('.user-' + model.get('id')).text(
        model.get('name') + (email ? ' (' + email + ')' : '') +
        ' - ' + text);
    },
    onOk: function() {
      if (this.$('.ok').text() === 'Close') {
        this.close();
        return;
      }
      this.setLoading('Emailing users...');

      var i;
      var model;
      var users = this.collection.models.slice(0);
      var error = false;
      var count = users.length;
      var linkDomain = window.location.protocol + '//' +
            window.location.host;
      var close = function() {
        if (!error) {
          this.setAlert('success', 'Successfully emailed selected users.');
        }
        this.$('.ok').text('Close');
        this.$('.cancel').hide();
        this.clearLoading();
      }.bind(this);
      var saveData = {
        success: function(model) {
          this.setUserText(model, 'success-text-light', 'Sent');
          if (--count < 1) {
            close();
          }
        }.bind(this),
        error: function(model, response) {
          this.setUserText(model, 'error-text-light', 'Failed');
          if (!error) {
            error = true;
            if (response.responseJSON) {
              this.setAlert('danger', response.responseJSON.error_msg);
            }
            else {
              this.setAlert('danger',
                'Failed to email users, server error occurred.');
            }
          }
          if (--count < 1) {
            close();
          }
        }.bind(this)
      };
      if (!count) {
        this.close();
      }
      for (i = 0; i < users.length; i++) {
        model = users[i].clone();
        if (!model.get('email')) {
          this.setUserText(model, 'warning-text-light', 'Skipped');
          if (--count < 1) {
            close();
          }
          continue;
        }
        model.save({
          send_key_email: linkDomain
        }, saveData);
        this.setUserText(model, 'primary-text-light', 'Sending...');
      }
    }
  });

  return ModalEmailUsersView;
});
