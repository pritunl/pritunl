define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalModifyLocation.html'
], function($, _, Backbone, ModalView,
    modalModifyLocationTemplate) {
  'use strict';
  var ModalModifyLocationView = ModalView.extend({
    className: 'modify-location-modal',
    template: _.template(modalModifyLocationTemplate),
    title: 'Modify Location',
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

      this.setLoading('Saving location...');
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

  return ModalModifyLocationView;
});
