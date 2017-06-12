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
    className: 'add-org-modal',
    template: _.template(modalAddOrgTemplate),
    title: 'Add Organization',
    okText: 'Add',
    events: function() {
      return _.extend({
        'click .auth-toggle': 'onAuthSelect'
      }, ModalAddOrgView.__super__.events);
    },
    body: function() {
      return this.template();
    },
    getAuthSelect: function() {
      return this.$('.auth-toggle .selector').hasClass('selected');
    },
    setAuthSelect: function(state) {
      if (state) {
        this.$('.auth-toggle .selector').addClass('selected');
        this.$('.auth-toggle .selector-inner').show();
        this.$('.auth-token-form').slideDown(window.slideTime);
      } else {
        this.$('.auth-toggle .selector').removeClass('selected');
        this.$('.auth-toggle .selector-inner').hide();
        this.$('.auth-token-form').slideUp(window.slideTime);
      }
    },
    onAuthSelect: function() {
      this.setAuthSelect(!this.getAuthSelect());
    },
    onOk: function() {
      var name = this.$('.name input').val();
      var authApi = this.getAuthSelect();

      if (!name) {
        this.setAlert('danger', 'Name can not be empty.', '.name');
        return;
      }

      this.setLoading('Adding organization...');
      var orgModel = new OrgModel();
      orgModel.save({
        name: name,
        auth_api: authApi
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

  return ModalAddOrgView;
});
