define([
  'jquery',
  'underscore',
  'backbone',
  'models/authSession',
  'views/alert',
  'views/login',
  'views/dashboard',
  'views/users',
  'views/servers'
], function($, _, Backbone, AuthSessionModel, AlertView, LoginView,
    DashboardView, UsersView, ServersView) {
  'use strict';
  var Router = Backbone.Router.extend({
    routes: {
      '': 'dashboard',
      'dashboard': 'dashboard',
      'users': 'users',
      'servers': 'servers',
      'logout': 'logout',
      'logout/:alert': 'logout'
    },
    initialize: function(data) {
      this.data = data;
      this.listenTo(window.events, 'subscription_active',
        this.onSubscriptionActive);
      this.listenTo(window.events, 'subscription_inactive',
        this.onSubscriptionInactive);
    },
    onSubscriptionActive: function() {
      window.enterprise = true;
      $('body').addClass('enterprise');

      $('.user .tooltip-inner:contains(' +
        '"Show additional user information")').parent().remove();
      $('.user .tooltip-inner:contains(' +
        '"Hide additional user information")').parent().remove();
      var tooltipText = 'Show additional user information';
      $('.toggle-servers').tooltip('destroy');
      $('.toggle-servers').attr('title', tooltipText);
      $('.toggle-servers').attr('data-original-title', tooltipText);
      $('.toggle-servers').tooltip();
    },
    onSubscriptionInactive: function() {
      $('.user-servers').hide();
      $('.toggle-servers').removeClass('glyphicon-chevron-up');
      $('.toggle-servers').addClass('glyphicon-chevron-down');

      $('input.org-search').val('');
      $('input.org-search').trigger('keydown');

      window.enterprise = false;
      $('body').removeClass('enterprise');
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
