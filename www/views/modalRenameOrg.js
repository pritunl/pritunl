define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalRenameOrg.html'
], function($, _, Backbone, ModalView, modalRenameOrgTemplate) {
  'use strict';
  var ModalRenameOrgView = ModalView.extend({
    className: 'rename-org-modal',
    template: _.template(modalRenameOrgTemplate),
    title: 'Rename Organization',
    okText: 'Rename',
    body: function() {
      return this.template(this.model.toJSON());
    },
    onOk: function() {
      if (!this.$('input').val()) {
        this.setAlert('danger', 'Name can not be empty.', '.form-group');
        return;
      }
      this.setLoading('Renaming organization...');
      this.model.save({
        name: this.$('input').val()
      }, {
        success: function() {
          this.close(true);
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to rename organization, server error occurred.');
        }.bind(this)
      });
    }
  });

  return ModalRenameOrgView;
});
