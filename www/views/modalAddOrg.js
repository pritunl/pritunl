define([
  'jquery',
  'underscore',
  'backbone',
  'models/org',
  'views/modal',
  'text!templates/modalAddOrg.html'
], function($, _, Backbone, OrgModel, ModalView, modalAddOrgTemplate) {
  'use strict';
  var ModalAddOrgView = ModalView.extend({
    className: 'add-org-modal',
    template: _.template(modalAddOrgTemplate),
    title: 'Add Organization',
    okText: 'Add',
    body: function() {
      return this.template();
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
      this.setLoading('Adding organization...');
      var orgModel = new OrgModel();
      orgModel.save({
        name: this.$('input').val()
      }, {
        success: function() {
          this.close(true);
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to add user, server error occurred.');
          this.locked = false;
        }.bind(this)
      });
    }
  });

  return ModalAddOrgView;
});
