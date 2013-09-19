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
    initialize: function() {
      this.body = this.template({
        users: this.collection.toJSON()
      });
      this.render();
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
              this.triggerEvt = true;
              this.close();
            }
          }.bind(this),
          error: function() {
            this.setAlert('danger',
              'Failed to delete user, server error occurred.');
            this.locked = false;
          }.bind(this)
        });
      }
    },
    onRemove: function() {
      var i;
      if (!this.triggerEvt) {
        return;
      }
      this.trigger('deleted');
    }
  });

  return ModalDeleteUsersView;
});
