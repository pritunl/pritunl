define([
  'jquery',
  'underscore',
  'backbone',
  'models/link',
  'views/modal',
  'text!templates/modalModifyLink.html'
], function($, _, Backbone, LinkModel, ModalView, modalModifyLinkTemplate) {
  'use strict';
  var ModalModifyLinkView = ModalView.extend({
    className: 'modify-link-modal',
    template: _.template(modalModifyLinkTemplate),
    title: 'Modify Link',
    okText: 'Save',
    body: function() {
      return this.template(this.model.toJSON());
    },
    onOk: function() {
      var name = this.$('.name input').val();

      if (!name) {
        this.setAlert('danger', 'Name can not be empty.', '.name');
        return;
      }

      this.setLoading('Saving link...');
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

  return ModalModifyLinkView;
});
