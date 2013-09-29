define([
  'jquery',
  'underscore',
  'backbone',
  'googleAnalytics',
  'models/auth',
  'views/alert',
  'views/login',
  'views/dashboard',
  'views/users',
  'views/servers'
], function($, _, Backbone, GoogleAnalytics, AuthModel, AlertView, LoginView,
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
    },
    checkAuth: function(callback) {
      if (window.authenticated) {
        callback(true);
        return;
      }
      var authModel = new AuthModel();
      authModel.fetch({
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
        $('body').append(this.loginView.render().el);
      }.bind(this));
      return false;
    },
    dashboard: function() {
      this.auth(function() {
        $('header .navbar .nav li').removeClass('active');
        $('header .dashboard').addClass('active');

        var curView = this.data.view;
        this.data.view = new DashboardView();
        $(this.data.element).fadeOut(400, function() {
          if (curView) {
            curView = curView.destroy();
          }
          $(this.data.element).html(this.data.view.render().el);
          $(this.data.element).fadeIn(400);
        }.bind(this));
      }.bind(this));
    },
    users: function() {
      this.auth(function() {
        $('header .navbar .nav li').removeClass('active');
        $('header .users').addClass('active');

        var curView = this.data.view;
        this.data.view = new UsersView();
        $(this.data.element).fadeOut(400, function() {
          if (curView) {
            curView = curView.destroy();
          }
          $(this.data.element).html(this.data.view.render().el);
          $(this.data.element).fadeIn(400);
        }.bind(this));
      }.bind(this));
    },
    servers: function() {
      this.auth(function() {
        $('header .navbar .nav li').removeClass('active');
        $('header .servers').addClass('active');

        var curView = this.data.view;
        this.data.view = new ServersView();
        $(this.data.element).fadeOut(400, function() {
          if (curView) {
            curView = curView.destroy();
          }
          $(this.data.element).html(this.data.view.render().el);
          $(this.data.element).fadeIn(400);
        }.bind(this));
      }.bind(this));
    },
    logout: function(alert) {
      if (alert === 'expired') {
        this.logoutAlert = 'Session has expired, please log in again';
      }
      var authModel = new AuthModel({
        id: true
      });
      authModel.destroy({
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
    var _loadUrl = Backbone.History.prototype.loadUrl;

    Backbone.ajax = function(options) {
      options.complete = function(response) {
        if (response.status === 401) {
          window.authenticated = false;
          Backbone.history.navigate('logout/expired', {trigger: true});
        }
      };
      return Backbone.$.ajax.call(Backbone.$, options);
    };

    Backbone.History.prototype.loadUrl = function() {
      var matched = _loadUrl.apply(this, arguments);

      var fragment = Backbone.history.getFragment();
      if (!/^\//.test(fragment)) {
        fragment = '/' + fragment;
      }

      // Send all url changes to analytics
      GoogleAnalytics.push(['_trackPageview', fragment]);

      return matched;
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
