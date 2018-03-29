define([
  'jquery',
  'underscore',
  'backbone',
  'models/linkExclude',
  'views/modal',
  'text!templates/modalAddLocExclude.html'
], function($, _, Backbone, LinkExcludeModel, ModalView,
    modalAddLocExcludeTemplate) {
  'use strict';
  var ModalAddLocExcludeView = ModalView.extend({
    className: 'add-location-exclude-modal',
    template: _.template(modalAddLocExcludeTemplate),
    title: 'Add Location Exclude',
    okText: 'Add',
    initialize: function(options) {
      this.link = options.link;
      this.location = options.location;
      this.locations = options.locations;
      ModalAddLocExcludeView.__super__.initialize.call(this);
    },
    body: function() {
      return this.template({
        location_id: this.location,
        locations: this.locations.toJSON()
      });
    },
    onOk: function() {
      var excludeId = this.$('.exclude-id select').val();

      if (!excludeId) {
        this.setAlert('danger', 'Missing exclude.', '.exclude-id');
        return;
      }

      this.setLoading('Adding location exclude...');
      var model = new LinkExcludeModel();
      model.save({
        link_id: this.link,
        location_id: this.location,
        exclude_id: excludeId
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

  return ModalAddLocExcludeView;
});
