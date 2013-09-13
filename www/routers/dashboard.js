define([
  'jquery',
  'underscore',
  'backbone',
  'views/dashboard/dashboard'
], function($, _, Backbone, DashboardView) {
  'use strict';
  var DashboardRouter = Backbone.Router.extend({
    routes: {
      '': 'dashboard',
      'dashboard': 'dashboard'
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
    }
  });

  return DashboardRouter;
});
