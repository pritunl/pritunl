define([
  'jquery',
  'underscore',
  'backbone',
  'models/auth',
  'models/subscription',
  'views/alert',
  'views/login',
  'views/modalSubscribe',
  'views/modalEnterprise',
  'text!templates/header.html'
], function($, _, Backbone, AuthModel, SubscriptionModel, AlertView, LoginView,
    ModalSubscribeView, ModalEnterpriseView, headerTemplate) {
  'use strict';
  var HeaderView = Backbone.View.extend({
    tagName: 'header',
    template: _.template(headerTemplate),
    events: {
      'click .enterprise-upgrade a': 'onEnterpriseUpgrade',
      'click .enterprise-settings a': 'onEnterpriseSettings',
      'click .change-password a': 'changePassword'
    },
    render: function() {
      this.$el.html(this.template());
      return this;
    },
    onEnterpriseUpgrade: function() {
      var modal = new ModalSubscribeView();
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Welcome to Pritunl Enterprise.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    onEnterpriseSettings: function() {
      var model = new SubscriptionModel();
      model.fetch({
        success: function() {
          var modal = new ModalEnterpriseView({
            model: model
          });
          this.listenToOnce(modal, 'applied', function() {
            var alertView = new AlertView({
              type: 'danger',
              message: 'Enterprise license removed.',
              dismissable: true
            });
            $('.alerts-container').append(alertView.render().el);
            this.addView(alertView);
          }.bind(this));
          this.addView(modal);
        }.bind(this),
      })
    },
    changePassword: function() {
      var loginView = new LoginView({
        showChangePassword: true
      });
      if (loginView.active) {
        $('body').append(loginView.render().el);
        this.addView(loginView);
      }
    }
  });

  return HeaderView;
});
