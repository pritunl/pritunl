define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalDeleteLocPeer.html'
], function($, _, Backbone, ModalView, AlertView,
    modalDeleteLocPeerTemplate) {
  'use strict';
  var ModalDeleteLocPeerView = ModalView.extend({
    className: 'delete-location-peer-modal',
    template: _.template(modalDeleteLocPeerTemplate),
    title: 'Remove Location Peer',
    okText: 'Remove',
    body: function() {
      return this.template(this.model.toJSON());
    },
    onOk: function() {
      this.setLoading('Removing location peer...');
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

  return ModalDeleteLocPeerView;
});
