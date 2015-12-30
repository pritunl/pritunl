define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalRenameOrg.html'
], function($, _, Backbone, ModalView, modalRenameOrgTemplate) {
  'use strict';
  var ModalRenameOrgView = ModalView.extend({
    className: 'rename-org-modal',
    template: _.template(modalRenameOrgTemplate),
    title: 'Modify Organization',
    okText: 'Modify',
    events: function() {
      return _.extend({
        'click .auth-toggle': 'onAuthSelect',
        'click .auth-token input, .auth-secret input': 'onClickInput',
        'click .generate-new-auth-key': 'onGenerateNewKey'
      }, ModalRenameOrgView.__super__.events);
    },
    body: function() {
      return this.template(this.model.toJSON());
    },
    update: function() {
      this.$('.auth-token input').val(this.model.get('auth_token'));
      this.$('.auth-secret input').val(this.model.get('auth_secret'));
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
    onClickInput: function(evt) {
      this.$(evt.target).select();
    },
    onGenerateNewKey: function() {
      this.setLoading('Generating new authorization key...');
      this.model.save({
        auth_token: true,
        auth_secret: true
      }, {
        success: function() {
          this.clearLoading();
          this.setAlert(
            'success', 'Successfully generated a new authorization key.');
          this.update();
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
    },
    onOk: function() {
      var name = this.$('.name input').val();
      var authApi = this.getAuthSelect();

      if (!name) {
        this.setAlert('danger', 'Name can not be empty.', '.name');
        return;
      }

      this.setLoading('Modifying organization...');
      this.model.save({
        name: name,
        auth_api: authApi,
        auth_token: null,
        auth_secret: null
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

  return ModalRenameOrgView;
});
