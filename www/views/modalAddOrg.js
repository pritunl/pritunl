define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalAddOrg.html'
], function($, _, Backbone, ModalView, AlertView, modalAddOrgTemplate) {
  'use strict';
  var ModalAddOrgView = ModalView.extend({
    template: _.template(modalAddOrgTemplate),
    title: 'Add Organization',
    okText: 'Add',
    initialize: function(options) {
      this.body = this.template();
      this.render();
    },
    alert: function() {
      if (this.alertView) {
        this.alertView.close(function() {
          this.alertView = null;
          this.alert();
        }.bind(this));
        return;
      }

      this.alertView = new AlertView({
        type: 'danger',
        message: 'Name can not be empty.'
      });
      this.$('form').prepend(this.alertView.render().el);
    },
    onOk: function() {
      if (!this.$('input').val()) {
        this.alert();
        return;
      }
      this.close();
    }
  });

  return ModalAddOrgView;
});
