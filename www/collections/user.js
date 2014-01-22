define([
  'jquery',
  'underscore',
  'backbone',
  'models/user'
], function($, _, Backbone, UserModel) {
  'use strict';
  var UserCollection = Backbone.Collection.extend({
    model: UserModel,
    initialize: function(options) {
      this.org = options.org;
      window.user_page = window.user_page || {};
      this.page = window.user_page[this.org] || 0;
    },
    url: function() {
      return '/user/' + this.org;
    },
    parse: function(response) {
      this.setPage(response.page);
      this.pageTotal = response.page_total;
      return response.users;
    },
    setPage: function(page) {
      this.page = page;
      window.user_page[this.org] = page;
    },
    getPage: function() {
      return this.page;
    },
    nextPage: function() {
      this.page += 1;
    },
    prevPage: function() {
      this.page -= 1;
    },
    isLastPage: function() {
      return this.page === this.pageTotal;
    }
  });

  return UserCollection;
});
