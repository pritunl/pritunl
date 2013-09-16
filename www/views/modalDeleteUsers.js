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
    initialize: function(options) {
      this.body = this.template({
        users: options.users.toJSON()
      });
      this.render();
    },
    onOk: function() {
      this.removedOrg = true;
      this.clearAlert();
      this.close();
    },
    onRemove: function() {
      if (!this.removedOrg) {
        return;
      }

      var alertView = new AlertView({
        type: 'warning',
        message: 'Successfully deleted users.',
        dismissable: true
      });
      $('.alerts-container').append(alertView.render().el);
    }
  });

  return ModalDeleteUsersView;
});
