define([
  'jquery',
  'underscore',
  'backbone',
  'googleAnalytics',
  'models/auth',
  'views/login',
  'views/dashboard',
  'views/users',
  'views/servers'
], function($, _, Backbone, GoogleAnalytics, AuthModel, LoginView,
    DashboardView, UsersView, ServersView) {
  'use strict';
  var Router = Backbone.Router.extend({
    routes: {
      '': 'dashboard',
      'dashboard': 'dashboard',
      'users': 'users',
      'servers': 'servers'
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
        var loginView = new LoginView({
          callback: function() {
            window.authenticated = true;
            loginView.destroy();
            callback();
          }.bind(this)
        });
        $('body').append(loginView.render().el);
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
    }
  });

  var initialize = function() {
    var _loadUrl = Backbone.History.prototype.loadUrl;

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
