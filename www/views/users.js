define([
  'jquery',
  'underscore',
  'backbone',
  'views/orgsList'
], function($, _, Backbone, OrgsListView) {
  'use strict';
  var UsersView = Backbone.View.extend({
    className: 'users container',
    initialize: function() {
      this.orgsList = new OrgsListView();
      this.addView(this.orgsList);
    },
    render: function() {
      this.$el.append(this.orgsList.render().el);
      return this;
    }
  });

  return UsersView;
});
