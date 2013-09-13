define([
  'jquery',
  'underscore',
  'backbone',
  'googleAnalytics',
  'routers/dashboard'
], function($, _, Backbone, GoogleAnalytics, DashboardRouter) {
  'use strict';
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

    new DashboardRouter(data);

    Backbone.history.start();
  };

  return {
    initialize: initialize
  };
});
