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
      this.users = options.users.models.slice(0);
      this.body = this.template({
        users: options.users.toJSON()
      });
      this.render();
    },
    onOk: function() {
      this.triggerEvt = true;
      this.close();
    },
    onRemove: function() {
      var i;
      if (!this.triggerEvt) {
        return;
      }
      for (i = 0; i < this.users.length; i++) {
        this.users[i].destroy();
      }
      this.trigger('deleted');
    }
  });

  return ModalDeleteUsersView;
});
