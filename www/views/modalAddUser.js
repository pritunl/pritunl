define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalAddUser.html'
], function($, _, Backbone, ModalView, modalAddUserTemplate) {
  'use strict';
  var ModalAddUserView = ModalView.extend({
    template: _.template(modalAddUserTemplate),
    title: 'Add User',
    okText: 'Add',
    initialize: function(options) {
      this.children = [];
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
      this.clearAlert();
      this.close();
    }
  });

  return ModalAddUserView;
});
