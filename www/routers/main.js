define([
  'jquery',
  'underscore',
  'backbone',
  'googleAnalytics',
  'views/dashboard',
  'views/users'
], function($, _, Backbone, GoogleAnalytics, DashboardView, UsersView) {
  'use strict';
  var Router = Backbone.Router.extend({
    routes: {
      '': 'dashboard',
      'dashboard': 'dashboard',
      'users': 'users'
    },
    initialize: function(data) {
      this.data = data;
    },
    dashboard: function() {
      $('header .navbar .nav li').removeClass('active');
      $('header .dashboard').addClass('active');

      if (this.data.view) {
        this.data.view.remove();
      }
      this.data.view = new DashboardView();
      $(this.data.element).fadeOut(400, function() {
        $(this.data.element).html(this.data.view.render().el);
        $(this.data.element).fadeIn(400);
      }.bind(this));
    },
    users: function() {
      $('header .navbar .nav li').removeClass('active');
      $('header .users').addClass('active');

      if (this.data.view) {
        this.data.view.remove();
      }
      this.data.view = new UsersView();
      $(this.data.element).fadeOut(400, function() {
        $(this.data.element).html(this.data.view.render().el);
        $(this.data.element).fadeIn(400);
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
