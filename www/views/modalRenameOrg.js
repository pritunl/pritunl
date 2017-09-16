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
    title: 'Modify Organization',
    okText: 'Modify',
    body: function() {
      return this.template(this.model.toJSON());
    },
    onOk: function() {
      var name = this.$('.name input').val();

      if (!name) {
        this.setAlert('danger', 'Name can not be empty.', '.name');
        return;
      }

      this.setLoading('Modifying organization...');
      this.model.save({
        name: name
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

  return ModalRenameOrgView;
});
