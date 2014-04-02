define([
  'jquery',
  'underscore',
  'backbone',
  'models/auth',
  'views/alert',
  'views/login',
  'views/modalSubscribe',
  'text!templates/header.html'
], function($, _, Backbone, AuthModel, AlertView, LoginView,
    ModalSubscribeView, headerTemplate) {
  'use strict';
  var HeaderView = Backbone.View.extend({
    tagName: 'header',
    template: _.template(headerTemplate),
    events: {
      'click .enterprise-upgrade a': 'onEnterpriseUpgrade',
      'click .change-password a': 'changePassword'
    },
    render: function() {
      this.$el.html(this.template());
      return this;
    },
    onEnterpriseUpgrade: function() {
      var modal = new ModalSubscribeView();
      this.addView(modal);
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
