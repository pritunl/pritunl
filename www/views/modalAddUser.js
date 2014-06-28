define([
  'jquery',
  'underscore',
  'backbone',
  'models/user',
  'views/modal',
  'text!templates/modalAddUser.html'
], function($, _, Backbone, UserModel, ModalView, modalAddUserTemplate) {
  'use strict';
  var ModalAddUserView = ModalView.extend({
    className: 'add-user-modal',
    template: _.template(modalAddUserTemplate),
    title: 'Add User',
    okText: 'Add',
    initialize: function(options) {
      this.orgs = options.orgs;
      ModalAddUserView.__super__.initialize.call(this);
    },
    body: function() {
      return this.template({
        orgs: this.orgs.toJSON()
      });
    },
    onOk: function() {
      var name = this.$('.name input').val();
      var org = this.$('.org select').val();
      var email = this.$('.email input').val();
      var emailReg = /^\w+([-+.']\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/;

      if (!name) {
        this.setAlert('danger', 'Name can not be empty.', '.form-group.name');
        return;
      }
      if (!email) {
        email = null;
      }
      else if (!emailReg.test(email)) {
        this.setAlert('danger', 'Email is not valid.', '.form-group.email');
        return;
      }

      this.setLoading('Adding user...');
      var userModel = new UserModel();
      userModel.save({
        organization: org,
        name: name,
        email: email
      }, {
        success: function() {
          this.close(true);
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to add user, server error occurred.');
        }.bind(this)
      });
    }
  });

  return ModalAddUserView;
});
