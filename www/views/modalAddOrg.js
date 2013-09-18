define([
  'jquery',
  'underscore',
  'backbone',
  'models/org',
  'views/modal',
  'text!templates/modalAddOrg.html'
], function($, _, Backbone, OrgModel, ModalView, modalAddOrgTemplate) {
  'use strict';
  var ModalAddOrgView = ModalView.extend({
    template: _.template(modalAddOrgTemplate),
    title: 'Add Organization',
    okText: 'Add',
    initialize: function(options) {
      this.body = this.template();
      this.render();
    },
    onOk: function() {
      if (this.locked) {
        return;
      }
      if (!this.$('input').val()) {
        this.setAlert('danger', 'Name can not be empty.');
        return;
      }
      this.locked = true;
      this.setLoading('Adding organization...');
      var orgModel = new OrgModel();
      orgModel.save({
        name: this.$('input').val()
      }, {
        success: function() {
          this.triggerEvt = true;
          this.close();
        }.bind(this),
        error: function() {
          this.setAlert('danger',
            'Failed to add user, server error occurred.');
        }.bind(this)
      });
    },
    onRemove: function() {
      if (!this.triggerEvt) {
        return;
      }
      this.trigger('added');
    }
  });

  return ModalAddOrgView;
});
