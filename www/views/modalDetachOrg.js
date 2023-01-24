define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalDetachOrg.html'
], function($, _, Backbone, ModalView, AlertView, modalDetachOrgTemplate) {
  'use strict';
  var ModalDetachOrgView = ModalView.extend({
    className: 'detach-org-modal',
    template: _.template(modalDetachOrgTemplate),
    title: 'Detach Organization',
    okText: 'Detach',
    initialize: function() {
      ModalDetachOrgView.__super__.initialize.call(this);
      this.setAlert('warning', 'Detaching an organization will require ' +
        'users that are not using an official Pritunl client to download ' +
        'their updated profile again before being able to connect. Users ' +
        'using an official Pritunl client will be able sync the changes.');
    },
    body: function() {
      return this.template(this.model.toJSON());
    },
    onOk: function() {
      this.setLoading('Detaching organization...');
      this.model.destroy({
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

  return ModalDetachOrgView;
});
