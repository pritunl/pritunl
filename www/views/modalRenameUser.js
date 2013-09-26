define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalRenameUser.html'
], function($, _, Backbone, ModalView, modalRenameUserTemplate) {
  'use strict';
  var ModalRenameUserView = ModalView.extend({
    className: 'rename-user-modal',
    template: _.template(modalRenameUserTemplate),
    title: 'Rename User',
    okText: 'Rename',
    body: function() {
      return this.template(this.model.toJSON());
    },
    onOk: function() {
      if (this.locked) {
        return;
      }
      if (!this.$('input').val()) {
        this.setAlert('danger', 'Name can not be empty.', '.form-group');
        return;
      }
      this.locked = true;
      this.setLoading('Renaming user...');
      this.model.save({
        name: this.$('input').val()
      }, {
        success: function() {
          this.close(true);
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to rename user, server error occurred.');
          this.locked = false;
        }.bind(this)
      });
    }
  });

  return ModalRenameUserView;
});
