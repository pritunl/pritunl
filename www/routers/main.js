define([
  'jquery',
  'underscore',
  'backbone',
  'models/authSession',
  'views/alert',
  'views/login',
  'views/dashboard',
  'views/users',
  'views/servers',
  'views/hosts'
], function($, _, Backbone, AuthSessionModel, AlertView, LoginView,
    DashboardView, UsersView, ServersView, HostsView) {
  'use strict';
  var Router = Backbone.Router.extend({
    routes: {
      '': 'dashboard',
      'dashboard': 'dashboard',
      'users': 'users',
      'servers': 'servers',
      'hosts': 'hosts',
      'logout': 'logout',
      'logout/:alert': 'logout'
    },
    initialize: function(data) {
      this.data = data;
      this.listenTo(window.events, 'subscription_none_active',
        this.onSubscriptionNoneActive);
      this.listenTo(window.events, 'subscription_premium_active',
        this.onSubscriptionPremiumActive);
      this.listenTo(window.events, 'subscription_enterprise_active',
        this.onSubscriptionEnterpriseActive);
      this.listenTo(window.events, 'subscription_none_inactive',
        this.onSubscriptionNoneInactive);
      this.listenTo(window.events, 'subscription_premium_inactive',
        this.onSubscriptionPremiumInactive);
      this.listenTo(window.events, 'subscription_enterprise_inactive',
        this.onSubscriptionEnterpriseInactive);
    },
    onSubscriptionPremiumActive: function() {
      window.subActive = true;
      window.subPlan = 'premium';
      $('body').addClass('premium');
      $('body').removeClass('enterprise');
      $('body').removeClass('premium-license');
      $('body').removeClass('enterprise-license');
    },
    onSubscriptionEnterpriseActive: function() {
      window.subActive = true;
      window.subPlan = 'enterprise';
      $('body').removeClass('premium');
      $('body').addClass('enterprise');
      $('body').removeClass('premium-license');
      $('body').removeClass('enterprise-license');
    },
    onSubscriptionPremiumInactive: function() {
      window.subActive = false;
      window.subPlan = 'premium';
      $('body').removeClass('premium');
      $('body').removeClass('enterprise');
      $('body').addClass('premium-license');
      $('body').removeClass('enterprise-license');
    },
    onSubscriptionEnterpriseInactive: function() {
      window.subActive = false;
      window.subPlan = 'enterprise';
      $('body').removeClass('premium');
      $('body').removeClass('enterprise');
      $('body').removeClass('premium-license');
      $('body').addClass('enterprise-license');
    },
    onSubscriptionNoneInactive: function() {
      window.subActive = false;
      window.subPlan = null;
      $('body').removeClass('premium');
      $('body').removeClass('enterprise');
      $('body').removeClass('premium-license');
      $('body').removeClass('enterprise-license');
    },
    checkAuth: function(callback) {
      if (window.authenticated) {
        callback(true);
        return;
      }
      var authSessionModel = new AuthSessionModel();
      authSessionModel.fetch({
        success: function(model) {
          if (model.get('authenticated')) {
            window.authenticated = true;
            callback(true);
          }
          else {
            callback(false);
          }
        },
        error: function() {
          callback(false);
        }
      });
    },
    auth: function(callback) {
      this.checkAuth(function(authStatus) {
        if (authStatus) {
          callback();
          return;
        }
        this.loginCallback = callback;
        if (this.loginView) {
          return;
        }
        $('.modal').modal('hide');
        this.loginView = new LoginView({
          alert: this.logoutAlert,
          callback: function() {
            this.loginView = null;
            window.authenticated = true;
            this.loginCallback();
            this.loginCallback = null;
          }.bind(this)
        });
        this.logoutAlert = null;
        if (this.loginView.active) {
          $('body').append(this.loginView.render().el);
        }
        else {
          this.loginView = null;
        }
      }.bind(this));
      return false;
    },
    loadPage: function(view) {
      var curView = this.data.view;
      this.data.view = view;
      $(this.data.element).fadeOut(100, function() {
        if (curView) {
          curView = curView.destroy();
        }
        $(this.data.element).html(this.data.view.render().el);
        $(this.data.element).fadeIn(300);
      }.bind(this));
    },
    dashboard: function() {
      this.auth(function() {
        $('header .navbar .nav li').removeClass('active');
        $('header .dashboard').addClass('active');
        this.loadPage(new DashboardView());
      }.bind(this));
    },
    users: function() {
      this.auth(function() {
        $('header .navbar .nav li').removeClass('active');
        $('header .users').addClass('active');
        this.loadPage(new UsersView());
      }.bind(this));
    },
    servers: function() {
      this.auth(function() {
        $('header .navbar .nav li').removeClass('active');
        $('header .servers').addClass('active');
        this.loadPage(new ServersView());
      }.bind(this));
    },
    hosts: function() {
      this.auth(function() {
        $('header .navbar .nav li').removeClass('active');
        $('header .hosts').addClass('active');
        this.loadPage(new HostsView());
      }.bind(this));
    },
    logout: function(alert) {
      if (alert === 'expired') {
        this.logoutAlert = 'Session has expired, please log in again';
      }
      var authSessionModel = new AuthSessionModel({
        id: true
      });
      authSessionModel.destroy({
        success: function() {
          window.authenticated = false;
          if (this.data.view) {
            Backbone.history.history.back();
          }
          else {
            this.navigate('', {trigger: true});
          }
        }.bind(this),
        error: function() {
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to logout, server error occurred.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          if (this.data.view) {
            this.data.view.addView(alertView);
          }
        }.bind(this)
      });
    }
  });

  var initialize = function() {
    var _ajax = Backbone.ajax;
    Backbone.ajax = function(options) {
      options.complete = function(response) {
        if (response.status === 401) {
          window.authenticated = false;
          Backbone.history.navigate('logout/expired', {trigger: true});
        }
      };
      return _ajax.call(Backbone.$, options);
    };

    var data = {
      element: '#app',
      view: null
    };

    var router = new Router(data);
    Backbone.history.start();
    return router;
  };

  return {
    initialize: initialize
  };
});
