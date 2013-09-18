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
    template: _.template(modalAddUserTemplate),
    title: 'Add User',
    okText: 'Add',
    initialize: function(options) {
      this.body = this.template({
        orgs: options.orgs.toJSON()
      });
      this.render();
    },
    onOk: function() {
      if (!this.$('input').val()) {
        this.setAlert('danger', 'Name can not be empty.');
        return;
      }
      var userModel = new UserModel({
        organization: this.$('select').val(),
        name: this.$('input').val()
      });
      userModel.save();
      this.clearAlert();
      this.close();
    }
  });

  return ModalAddUserView;
});
