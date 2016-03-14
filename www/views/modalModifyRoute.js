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
    hasAdvanced: false,
    events: function() {
      return _.extend({
        'click .nat-route-toggle': 'onNatRouteSelect'
      }, ModalModifyRouteView.__super__.events);
    },
    body: function() {
      return this.template(this.model.toJSON());
    },
    postRender: function() {
      this.$('.label').tooltip();
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
      var nat = this.getNatRouteSelect();
      var vpcRegion = this.$('.vpc-region select').val();
      var vpcId = this.$('.vpc-id input').val();

      this.setLoading('Modifying route...');
      this.model.save({
        nat: nat,
        vpc_region: vpcRegion,
        vpc_id: vpcId
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
