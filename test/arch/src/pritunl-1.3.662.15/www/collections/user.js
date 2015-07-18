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
      var hasKey = response.server_count ? true : false;

      if (response.page !== undefined) {
        this.setPage(response.page);
        this.setPageTotal(response.page_total);
      }
      else {
        this.setSearchTime(response.search_time);
        this.setSearchMore(response.search_more);
        this.setSearchCount(response.search_count);
        this.setSearchLimit(response.search_limit);
      }

      for (var i = 0; i < response.users.length; i++) {
        response.users[i].has_key = hasKey;
      }

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
    setPageTotal: function(total) {
      this.pageTotal = total;
    },
    getPageTotal: function() {
      return this.pageTotal;
    },
    setSearch: function(term) {
      this.search = term;
    },
    getSearch: function() {
      return this.search;
    },
    clearSearch: function() {
      this.search = null;
    },
    setSearchTime: function(time) {
      this.searchTime = time;
    },
    getSearchTime: function() {
      return this.searchTime.toFixed(4);
    },
    setSearchLimit: function(limit) {
      this.searchLimit = limit;
    },
    getSearchLimit: function() {
      return this.searchLimit;
    },
    setSearchMore: function(more) {
      this.searchMore = more;
    },
    getSearchMore: function() {
      return this.searchMore;
    },
    setSearchCount: function(count) {
      this.searchCount = count;
    },
    getSearchCount: function() {
      return this.searchCount;
    },
    isLastPage: function() {
      return this.page === this.pageTotal;
    }
  });

  return UserCollection;
});
