define([
  'jquery',
  'underscore',
  'backbone',
  'models/link',
  'views/modal',
  'text!templates/modalAddLink.html'
], function($, _, Backbone, LinkModel, ModalView, modalAddLinkTemplate) {
  'use strict';
  var ModalAddLinkView = ModalView.extend({
    className: 'add-link-modal',
    template: _.template(modalAddLinkTemplate),
    title: 'Add Link',
    okText: 'Add',
    body: function() {
      return this.template();
    },
    onOk: function() {
      var name = this.$('.name input').val();
      var linkType = this.$('.link-type select').val();

      if (!name) {
        this.setAlert('danger', 'Name can not be empty.', '.name');
        return;
      }

      this.setLoading('Adding link...');
      var model = new LinkModel();
      model.save({
        name: name,
        type: linkType
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

  return ModalAddLinkView;
});
