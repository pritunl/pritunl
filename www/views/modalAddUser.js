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
      var userModel = new UserModel();
      userModel.save({
        organization: this.$('select').val(),
        name: this.$('input').val()
      }, {
        success: function() {
          this.triggerEvt = true;
          this.clearAlert();
          this.close();
        }.bind(this),
        error: function() {
          this.setAlert('danger',
            'Failed to add user, server error occurred.');
        }.bind(this)
      });
    },
    onRemove: function() {
      if (!this.triggerEvt) {
        return;
      }
      this.trigger('added');
    }
  });

  return ModalAddUserView;
});
