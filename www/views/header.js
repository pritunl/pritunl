define([
  'jquery',
  'underscore',
  'backbone',
  'models/settings',
  'models/subscription',
  'models/user',
  'collections/userAudit',
  'views/alert',
  'views/modalLogs',
  'views/modalSettings',
  'views/modalSubscribe',
  'views/modalEnterprise',
  'text!templates/header.html'
], function($, _, Backbone, SettingsModel, SubscriptionModel, UserModel,
    UserAuditCollection, AlertView, ModalLogsView, ModalSettingsView,
    ModalSubscribeView, ModalEnterpriseView, headerTemplate) {
  'use strict';
  var HeaderView = Backbone.View.extend({
    tagName: 'header',
    template: _.template(headerTemplate),
    events: {
      'click .enterprise-upgrade a': 'onEnterprise',
      'click .enterprise-plus-upgrade a': 'onEnterprise',
      'click .enterprise-settings a': 'onEnterprise',
      'click .logs a': 'openLogs',
      'click .change-password a': 'openSettings'
    },
    initialize: function() {
      this.model = new SettingsModel();
      this.listenTo(window.events, 'settings_updated', this.update);
      this.update();
      HeaderView.__super__.initialize.call(this);
    },
    render: function() {
      this.$el.html(this.template());
      return this;
    },
    update: function() {
      this.model.fetch({
        success: function(model) {
          if (model.get('auditing') === 'all') {
            this.$('.audit-admin a').css('display', 'block');
          }
          else {
            this.$('.audit-admin a').hide();
          }
        }.bind(this),
        error: function() {
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to load settings data, ' +
              'server error occurred.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
        }.bind(this)
      });
    },
    onEnterprise: function() {
      if (this.onEnterpriseLock) {
        return;
      }
      this.onEnterpriseLock = true;
      var model = new SubscriptionModel();
      model.fetch({
        success: function(model) {
          if (model.get('plan')) {
            this.enterpriseSettings(model);
          }
          else {
            this.enterpriseUpgrade();
          }
          this.onEnterpriseLock = false;
        }.bind(this),
        error: function() {
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to load subscription information, ' +
              'server error occurred.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
          this.onEnterpriseLock = false;
        }.bind(this)
      });
    },
    enterpriseUpgrade: function() {
      var modal = new ModalSubscribeView();
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'License activated.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    enterpriseSettings: function(model) {
      var modal = new ModalEnterpriseView({
        model: model
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'danger',
          message: 'License removed.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    openLogs: function() {
      var modal = new ModalLogsView();
      this.addView(modal);
    },
    openSettings: function() {
      var model = new SettingsModel();
      model.fetch({
        success: function() {
          var modal = new ModalSettingsView({
            model: model
          });
          this.listenToOnce(modal, 'applied', function() {
            var alertView = new AlertView({
              type: 'success',
              message: 'Successfully saved settings.',
              dismissable: true
            });
            $('.alerts-container').append(alertView.render().el);
            this.addView(alertView);
          }.bind(this));
          this.addView(modal);
        }.bind(this),
        error: function() {
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to load settings data, ' +
              'server error occurred.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
        }.bind(this)
      });
    }
  });

  return HeaderView;
});
