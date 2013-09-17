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
    template: _.template(modalDeleteOrgTemplate),
    title: 'Delete Organization',
    okText: 'Delete',
    initialize: function(options) {
      this.body = this.template();
      this.render();

      var alertView = new AlertView({
        type: 'danger',
        message: 'Deleting the organization will delete all the users in it.',
        animate: false
      });
      this.addView(alertView);
      this.$('form').prepend(alertView.render().el);
    },
    onOk: function() {
      if (this.$('input').val() !== this.model.get('name')) {
        this.setAlert('info', 'Name entered doesn\'t match the name' +
          'of the organization being deleted.');
        return;
      }
      this.removedOrg = true;
      this.clearAlert();
      this.close();
    },
    onRemove: function() {
      if (!this.removedOrg) {
        return;
      }

      // TODO Not watched for destroy
      var alertView = new AlertView({
        type: 'warning',
        message: 'Successfully deleted organization.',
        dismissable: true
      });
      $('.alerts-container').append(alertView.render().el);
    }
  });

  return ModalDeleteOrgView;
});
