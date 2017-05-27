define([
  'jquery',
  'underscore',
  'backbone',
  'models/linkHost',
  'views/modal',
  'text!templates/modalAddLocHost.html'
], function($, _, Backbone, LinkHostModel, ModalView,
    modalAddLocHostTemplate) {
  'use strict';
  var ModalAddLocHostView = ModalView.extend({
    className: 'add-location-host-modal',
    template: _.template(modalAddLocHostTemplate),
    title: 'Add Location Host',
    okText: 'Add',
    initialize: function(options) {
      this.link = options.link;
      this.location = options.location;
      ModalAddLocHostView.__super__.initialize.call(this);
    },
    body: function() {
      return this.template();
    },
    onOk: function() {
      var name = this.$('.name input').val();
      var timeout = parseInt(this.$('.timeout input').val(), 10) || null;
      var priority = parseInt(this.$('.priority input').val(), 10) || 1;

      if (!name) {
        this.setAlert('danger', 'Name can not be empty.', '.name');
        return;
      }

      this.setLoading('Adding location host...');
      var model = new LinkHostModel();
      model.save({
        link_id: this.link,
        location_id: this.location,
        name: name,
        timeout: timeout,
        priority: priority
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

  return ModalAddLocHostView;
});
