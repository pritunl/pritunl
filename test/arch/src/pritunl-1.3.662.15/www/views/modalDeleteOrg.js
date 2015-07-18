define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalDeleteOrg.html'
], function($, _, Backbone, ModalView, AlertView, modalDeleteOrgTemplate) {
  'use strict';
  var ModalDeleteOrgView = ModalView.extend({
    className: 'delete-org-modal',
    template: _.template(modalDeleteOrgTemplate),
    title: 'Delete Organization',
    okText: 'Delete',
    inputMatch: true,
    initialize: function() {
      ModalDeleteOrgView.__super__.initialize.call(this);
      var alertView = new AlertView({
        type: 'danger',
        message: 'Deleting the organization will delete all the users ' +
          'in it. Any servers that are attached to the organization will ' +
          'be stopped.',
        animate: false
      });
      this.addView(alertView);
      this.$('.modal-body').prepend(alertView.render().el);
      this.inputMatchText = this.model.get('name');
    },
    body: function() {
      return this.template();
    },
    onOk: function() {
      this.setLoading('Deleting organization...');
      this.model.destroy({
        success: function() {
          this.close(true);
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to delete organization, server error occurred.');
        }.bind(this)
      });
    }
  });

  return ModalDeleteOrgView;
});
