define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalModifyRoute.html'
], function($, _, Backbone, ModalView, modaleModifyRouteTemplate) {
  'use strict';
  var ModalModifyRouteView = ModalView.extend({
    className: 'modify-route-modal',
    template: _.template(modaleModifyRouteTemplate),
    title: 'Modify Route',
    okText: 'Save',
    hasAdvanced: true,
    events: function() {
      return _.extend({
        'change .vpc-region select': 'updateVpcIds',
        'click .route-advertisement-toggle': 'onRotueAdSelect',
        'click .nat-route-toggle': 'onNatRouteSelect',
        'click .net-gateway-toggle': 'onNetGatewaySelect'
      }, ModalModifyRouteView.__super__.events);
    },
    initialize: function() {
      ModalModifyRouteView.__super__.initialize.call(this);
    },
    body: function() {
      return this.template(this.model.toJSON());
    },
    postRender: function() {
      this.$('.label').tooltip();
    },
    updateVpcIds: function() {
      var curVpcId = this.model.get('vpc_id');

      var vpcRegion = this.$('.vpc-region select').val();
      var vpcs = this.vpcs.get(vpcRegion) || [];
      var vpcId;
      var vpcNet;
      var vpcLabel;

      if (!vpcs.length) {
        this.$('.vpc-id select').html(
          '<option selected value="">No VPCs available</option>');
        return;
      }

      this.$('.vpc-id select').empty();

      for (var i = 0; i < vpcs.length; i++) {
        vpcId = vpcs[i].id;
        vpcNet = vpcs[i].network;
        vpcLabel = vpcId + ' (' + vpcNet + ')';

        this.$('.vpc-id select').append(
          '<option ' + (vpcId === curVpcId ? 'selected' : '') + ' value="' +
            vpcId + '">' + vpcLabel + '</option>');
      }
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
    getNetGatewaySelect: function() {
      return this.$('.net-gateway-toggle .selector').hasClass('selected');
    },
    setNetGatewaySelect: function(state) {
      if (state) {
        this.$('.net-gateway-toggle .selector').addClass('selected');
        this.$('.net-gateway-toggle .selector-inner').show();
      }
      else {
        this.$('.net-gateway-toggle .selector').removeClass('selected');
        this.$('.net-gateway-toggle .selector-inner').hide();
      }
    },
    onNetGatewaySelect: function() {
      this.setNetGatewaySelect(!this.getNetGatewaySelect());
    },
    getRotueAdSelect: function() {
      return this.$('.route-advertisement-toggle .selector').hasClass(
        'selected');
    },
    setRotueAdSelect: function(state) {
      if (state) {
        this.$('.route-advertisement-toggle .selector').addClass('selected');
        this.$('.route-advertisement-toggle .selector-inner').show();
        this.$('.route-advertisement').slideDown(window.slideTime);
      }
      else {
        this.$('.route-advertisement-toggle .selector').removeClass(
          'selected');
        this.$('.route-advertisement-toggle .selector-inner').hide();
        this.$('.route-advertisement').slideUp(window.slideTime);
      }
    },
    onRotueAdSelect: function() {
      this.setRotueAdSelect(!this.getRotueAdSelect());
    },
    onOk: function() {
      var comment = this.$('.route-comment input').val();
      var metric = this.$('.route-metric input').val();
      var nat = this.getNatRouteSelect();
      var natInterface = this.$('.nat-interface input').val();
      var natNetmap = this.$('.nat-netmap input').val();
      var netGateway = this.getNetGatewaySelect();
      var routeAd = this.getRotueAdSelect();

      metric = metric ? parseInt(metric, 10) : null;

      this.setLoading('Modifying route...');
      this.model.save({
        comment: comment,
        metric: metric,
        nat: nat,
        nat_interface: natInterface,
        nat_netmap: natNetmap,
        net_gateway: netGateway,
        advertise: routeAd
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

  return ModalModifyRouteView;
});
