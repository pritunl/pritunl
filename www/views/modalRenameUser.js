define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalRenameUser.html'
], function($, _, Backbone, ModalView, modalRenameUserTemplate) {
  'use strict';
  var ModalRenameUserView = ModalView.extend({
    template: _.template(modalRenameUserTemplate),
    title: 'Rename User',
    okText: 'Rename',
    initialize: function(options) {
      this.body = this.template(this.model.toJSON());
      this.render();
    },
    onOk: function() {
      if (this.locked) {
        return;
      }
      if (!this.$('input').val()) {
        this.setAlert('danger', 'Name can not be empty.');
        return;
      }
      this.locked = true;
      this.setLoading('Renaming user...');
      this.model.save({
        name: this.$('input').val()
      }, {
        success: function() {
          this.triggerEvt = true;
          this.close();
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to rename user, server error occurred.');
          this.locked = false;
        }.bind(this)
      });
    },
    onRemove: function() {
      if (!this.triggerEvt) {
        return;
      }
      this.trigger('renamed');
    }
  });

  return ModalRenameUserView;
});
