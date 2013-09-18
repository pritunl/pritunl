define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalRenameUser.html'
], function($, _, Backbone, ModalView, modalRenameUserTemplate) {
  'use strict';
  var ModalRenameUserView = ModalView.extend({
    template: _.template(modalRenameUserTemplate),
    title: 'Rename User',
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

  return ModalRenameUserView;
});
