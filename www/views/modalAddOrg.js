define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalAddOrg.html'
], function($, _, Backbone, ModalView, modalAddOrgTemplate) {
  'use strict';
  var ModalAddOrgView = ModalView.extend({
    template: _.template(modalAddOrgTemplate),
    title: 'Add Organization',
    okText: 'Add',
    initialize: function(options) {
      this.body = this.template();
      this.render();
    },
    onOk: function() {
      if (!this.$('input').val()) {
        this.setAlert('danger', 'Name can not be empty.');
        return;
      }
      this.clearAlert();
      this.close();
    }
  });

  return ModalAddOrgView;
});
