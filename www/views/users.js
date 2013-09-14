define([
  'jquery',
  'underscore',
  'backbone',
  'views/organizationsList',
  'text!templates/users.html'
], function($, _, Backbone, OrganizationsListView, usersTemplate) {
  'use strict';
  var UsersView = Backbone.View.extend({
    className: 'users container',
    template: _.template(usersTemplate),
    render: function() {
      this.$el.html(this.template());

      this.organizationsList = new OrganizationsListView();
      this.$el.append(this.organizationsList.render().el);

      return this;
    }
  });

  return UsersView;
});
