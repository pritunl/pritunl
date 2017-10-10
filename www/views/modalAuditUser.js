define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalAuditUser.html'
], function($, _, Backbone, ModalView, AlertView, modalAuditUserTemplate) {
  'use strict';
  var ModalAuditUserView = ModalView.extend({
    className: 'audit-user-modal',
    template: _.template(modalAuditUserTemplate),
    title: 'User Audit',
    okText: 'Close',
    cancelText: null,
    body: function() {
      return this.template({
        user: this.collection.user.toJSON(),
        events: []
      });
    },
    postRender: function() {
      this.setLoading('Loading user audit...', true);
      this.collection.fetch({
        success: function() {
          this.clearLoading();
          if (!this.collection.length) {
            this.setAlert('info', 'User has no audit events', false, true);
          } else {
            this.$('.modal-body').append(this.template({
              user: {},
              events: this.collection.toJSON()
            }));
          }
        }.bind(this),
        error: function(model, response) {
          this.clearLoading();
          if (response.responseJSON) {
            this.setAlert('danger', response.responseJSON.error_msg);
          }
          else {
            this.setAlert('danger', this.errorMsg);
          }
        }.bind(this)
      });
    }
  });

  return ModalAuditUserView;
});
