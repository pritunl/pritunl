define([
  'jquery',
  'underscore',
  'backbone',
  'models/linkLocation',
  'views/modal',
  'text!templates/modalAddLocation.html'
], function($, _, Backbone, LinkLocationModel, ModalView,
    modalAddLocationTemplate) {
  'use strict';
  var lastLink;
  var ModalAddLocationView = ModalView.extend({
    className: 'add-location-modal',
    template: _.template(modalAddLocationTemplate),
    title: 'Add Link Location',
    okText: 'Add',
    initialize: function(options) {
      this.links = options.links;
      ModalAddLocationView.__super__.initialize.call(this);
    },
    body: function() {
      return this.template({
        links: this.links.toJSON(),
        lastLink: lastLink
      });
    },
    onOk: function() {
      var name = this.$('.name input').val();
      var link = this.$('.link select').val();

      if (!name) {
        this.setAlert('danger', 'Name can not be empty.', '.name');
        return;
      }

      this.setLoading('Adding location...');
      var model = new LinkLocationModel();
      model.save({
        name: name,
        link_id: link
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

  return ModalAddLocationView;
});
