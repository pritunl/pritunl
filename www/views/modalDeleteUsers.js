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
      this.triggerEvt = true;
      this.close();
    },
    onRemove: function() {
      var i;
      if (!this.triggerEvt) {
        return;
      }
      var users = this.collection.models.slice(0);
      for (i = 0; i < users.length; i++) {
        users[i].destroy();
      }
      this.trigger('deleted');
    }
  });

  return ModalDeleteUsersView;
});
