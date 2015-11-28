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
      if (!this.$('input').val()) {
        this.setAlert('danger', 'Name can not be empty.', '.form-group');
        return;
      }
      this.setLoading('Adding organization...');
      var orgModel = new OrgModel();
      orgModel.save({
        name: this.$('input').val()
      }, {
        success: function() {
          this.close(true);
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

  return ModalAddOrgView;
});
