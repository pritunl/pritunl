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
    initialize: function() {
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
      if (this.locked) {
        return;
      }
      if (this.$('input').val() !== this.model.get('name')) {
        this.setAlert('info', 'Name entered doesn\'t match the name' +
          'of the organization being deleted.');
        return;
      }
      this.locked = true;
      this.setLoading('Deleting organization...');
      this.model.destroy({
        success: function() {
          this.triggerEvt = true;
          this.close();
        }.bind(this),
        error: function() {
          this.setAlert('danger',
            'Failed to delet organization, server error occurred.');
          this.locked = false;
        }.bind(this)
      });
    },
    onRemove: function() {
      if (!this.triggerEvt) {
        return;
      }
      this.trigger('deleted');
    }
  });

  return ModalDeleteOrgView;
});
