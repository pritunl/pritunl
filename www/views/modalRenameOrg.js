define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalRenameOrg.html'
], function($, _, Backbone, ModalView, modalRenameOrgTemplate) {
  'use strict';
  var ModalRenameOrgView = ModalView.extend({
    template: _.template(modalRenameOrgTemplate),
    title: 'Rename Organization',
    okText: 'Rename',
    initialize: function(options) {
      this.body = this.template(this.model.toJSON());
      this.render();
    },
    onOk: function() {
      if (!this.$('input').val()) {
        this.setAlert('danger', 'Name can not be empty.');
        return;
      }
      this.close();
    }
  });

  return ModalRenameOrgView;
});
