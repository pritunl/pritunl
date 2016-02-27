define([
  'jquery',
  'underscore',
  'backbone',
  'models/serverRoute',
  'views/modal',
  'text!templates/modalAddRoute.html'
], function($, _, Backbone, ServerRouteModel, ModalView,
    modalAddRouteTemplate) {
  'use strict';
  var lastServer;
  var ModalAddRouteView = ModalView.extend({
    className: 'attach-org-modal',
    template: _.template(modalAddRouteTemplate),
    title: 'Add Route',
    okText: 'Attach',
    body: function() {
      return this.template({
        servers: this.collection.toJSON(),
        lastServer: lastServer
      });
    },
    onOk: function() {
      this.setLoading('Adding route...');
      var model = new ServerRouteModel();
      var server = this.$('.server select').val();
      lastServer = server;
      model.save({
        network: this.$('.route-network input').val(),
        server: server
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

  return ModalAddRouteView;
});
