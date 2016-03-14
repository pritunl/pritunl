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
    className: 'add-route-modal',
    template: _.template(modalAddRouteTemplate),
    title: 'Add Route',
    okText: 'Attach',
    events: function() {
      return _.extend({
        'click .nat-route-toggle': 'onNatRouteSelect'
      }, ModalAddRouteView.__super__.events);
    },
    body: function() {
      return this.template({
        servers: this.collection.toJSON(),
        lastServer: lastServer
      });
    },
    getNatRouteSelect: function() {
      return this.$('.nat-route-toggle .selector').hasClass('selected');
    },
    setNatRouteSelect: function(state) {
      if (state) {
        this.$('.nat-route-toggle .selector').addClass('selected');
        this.$('.nat-route-toggle .selector-inner').show();
      }
      else {
        this.$('.nat-route-toggle .selector').removeClass('selected');
        this.$('.nat-route-toggle .selector-inner').hide();
      }
    },
    onNatRouteSelect: function() {
      this.setNatRouteSelect(!this.getNatRouteSelect());
    },
    onOk: function() {
      this.setLoading('Adding route...');
      var model = new ServerRouteModel();

      var server = this.$('.server select').val();
      var nat = this.getNatRouteSelect();
      var vpcRegion = this.$('.vpc-region select').val();
      var vpcId = this.$('.vpc-id input').val();

      lastServer = server;
      model.save({
        network: this.$('.route-network input').val(),
        nat: nat,
        vpc_region: vpcRegion,
        vpc_id: vpcId,
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
