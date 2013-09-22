define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalDetachOrg.html'
], function($, _, Backbone, ModalView, AlertView, modalDetachOrgTemplate) {
  'use strict';
  var ModalDetachOrgView = ModalView.extend({
    className: 'detach-org-modal',
    template: _.template(modalDetachOrgTemplate),
    title: 'Detach Organization',
    okText: 'Detach',
    body: function() {
      return this.template(this.model.toJSON());
    },
    onOk: function() {
      if (this.locked) {
        return;
      }
      this.locked = true;
      this.setLoading('Detaching organization...');
      this.model.destroy({
        success: function() {
          this.close(true);
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to detach organization, server error occurred.');
          this.locked = false;
        }.bind(this)
      });
    }
  });

  return ModalDetachOrgView;
});
