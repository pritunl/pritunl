define([
  'jquery',
  'underscore',
  'backbone',
  'views/users/users'
], function($, _, Backbone, UsersView) {
  'use strict';
  var UsersRouter = Backbone.Router.extend({
    routes: {
      'users': 'users'
    },
    initialize: function(data) {
      this.data = data;
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

  return UsersRouter;
});
