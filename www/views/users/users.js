define([
  'jquery',
  'underscore',
  'backbone',
  'text!templates/users/users.html'
], function($, _, Backbone, usersTemplate) {
  'use strict';
  var UsersView = Backbone.View.extend({
    template: _.template(usersTemplate),
    render: function() {
      this.$el.html(this.template());
      return this;
    }
  });

  return UsersView;
});
