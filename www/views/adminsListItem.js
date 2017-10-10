define([
  'jquery',
  'underscore',
  'backbone',
  'models/key',
  'collections/adminAudit',
  'views/alert',
  'views/modalModifyAdmin',
  'views/modalKeyLink',
  'views/modalAuditUser',
  'views/modalOtpAuth',
  'views/userServersList',
  'text!templates/adminsListItem.html'
], function($, _, Backbone, KeyModel, AdminAuditCollection, AlertView,
    ModalModifyAdminView, ModalKeyLinkView, ModalAuditUserView,
    ModalOtpAuthView, UserServersListView, adminsListItemTemplate) {
  'use strict';
  var AdminsListItemView = Backbone.View.extend({
    template: _.template(adminsListItemTemplate),
    events: {
      'click .selector': 'onSelect',
      'click .admin-username': 'onModify',
      'click .audit-admin': 'onAuditAdmin',
      'click .get-otp-auth': 'onGetOtpAuth',
      'click .disable-admin': 'onDisableAdmin',
      'click .enable-admin': 'onEnableAdmin'
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      this.$('[data-toggle="tooltip"]').tooltip();
      if (this.model.get('disabled')) {
        this.$('.disable-admin').hide();
      }
      else {
        this.$('.enable-admin').hide();
      }
      return this;
    },
    update: function() {
      this.$('.admin-username').text(this.model.get('username'));

      if (this.model.get('disabled')) {
        this.$('.admin .status-icon').removeClass('online');
        this.$('.admin .status-icon').removeClass('offline');
        this.$('.admin .status-icon').addClass('disabled');
        this.$('.admin .status-text').text('Disabled');
        this.$('.disable-admin').hide();
        this.$('.enable-admin').show();
      } else {
        this.$('.user .status-icon').removeClass('disabled');
        this.$('.enable-admin').hide();
        this.$('.disable-admin').show();
      }

      if (this.model.get('otp_auth')) {
        this.$('.get-otp-auth').removeClass('no-otp-auth');
      } else {
        this.$('.get-otp-auth').addClass('no-otp-auth');
      }

      if (this.model.get('audit')) {
        this.$('.audit-admin').removeClass('no-audit-admin');
      }
      else {
        this.$('.audit-admin').addClass('no-audit-admin');
      }
    },
    getSelect: function() {
      return this.$('.selector').hasClass('selected');
    },
    setSelect: function(state, shiftKey) {
      if (state === this.getSelect()) {
        return;
      }

      if (state) {
        this.$('.selector').addClass('selected');
        this.$('.selector-inner').show();
      }
      else {
        this.$('.selector').removeClass('selected');
        this.$('.selector-inner').hide();
      }
      this.trigger('select', this, shiftKey);
    },
    onSelect: function(evt) {
      this.setSelect(!this.getSelect(), evt.shiftKey);
    },
    onModify: function() {
      var modal = new ModalModifyAdminView({
        model: this.model.clone()
      });
      this.addView(modal);
    },
    onAuditAdmin: function() {
      var modal = new ModalAuditUserView({
        collection: new AdminAuditCollection({
          user: this.model
        })
      });
      this.addView(modal);
    },
    onGetOtpAuth: function() {
      var modal = new ModalOtpAuthView({
        model: this.model
      });
      this.addView(modal);
    },
    onDisableAdmin: function() {
      if (this.$('.disable-admin').hasClass('disabled')) {
        return;
      }
      this.$('.disable-admin').addClass('disabled');
      this.model.save({
        disabled: true,
        otp_secret: null,
        token: null,
        secret: null
      }, {
        success: function() {
          this.$('.disable-admin').removeClass('disabled');
          this.update();
        }.bind(this),
        error: function(model, response) {
          var message;
          if (response.responseJSON) {
            message = response.responseJSON.error_msg;
          }
          else {
            message = 'Failed to disable administrator, ' +
              'server error occurred.';
          }

          var alertView = new AlertView({
            type: 'danger',
            message: message,
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
          this.$('.disable-admin').removeClass('disabled');
        }.bind(this)
      });
    },
    onEnableAdmin: function() {
      if (this.$('.enable-admin').hasClass('disabled')) {
        return;
      }
      this.$('.enable-admin').addClass('disabled');
      this.model.save({
        disabled: false,
        otp_secret: null,
        token: null,
        secret: null
      }, {
        success: function() {
          this.$('.enable-admin').removeClass('disabled');
          this.update();
        }.bind(this),
        error: function(model, response) {
          var message;
          if (response.responseJSON) {
            message = response.responseJSON.error_msg;
          }
          else {
            message = 'Failed to enable administrator, server error occurred.';
          }

          var alertView = new AlertView({
            type: 'danger',
            message: message,
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
          this.$('.enable-admin').removeClass('disabled');
        }.bind(this)
      });
    }
  });

  return AdminsListItemView;
});
