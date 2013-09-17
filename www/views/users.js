define([
  'jquery',
  'underscore',
  'backbone',
  'views/orgsList',
  'text!templates/users.html'
], function($, _, Backbone, OrgsListView, usersTemplate) {
  'use strict';
  var UsersView = Backbone.View.extend({
    className: 'users container',
    template: _.template(usersTemplate),
    initialize: function(options) {
      this.orgsList = new OrgsListView();
      this.addView(this.orgsList);
    },
    render: function() {
      this.$el.html(this.template());
      this.$el.append(this.orgsList.render().el);
      return this;
    }
  });

  return UsersView;
});
