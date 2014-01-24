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
    initialize: function() {
      ModalDetachOrgView.__super__.initialize.call(this);
      var alertView = new AlertView({
        type: 'danger',
        message: 'Detaching an organization may require users to ' +
          're-download their keys.',
        animate: false
      });
      this.addView(alertView);
      this.$('.modal-body').prepend(alertView.render().el);
    },
    body: function() {
      return this.template(this.model.toJSON());
    },
    onOk: function() {
      this.setLoading('Detaching organization...');
      this.model.destroy({
        success: function() {
          this.close(true);
        }.bind(this),
        error: function() {
          this.clearLoading();
          this.setAlert('danger',
            'Failed to detach organization, server error occurred.');
        }.bind(this)
      });
    }
  });

  return ModalDetachOrgView;
});
