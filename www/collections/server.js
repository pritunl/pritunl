define([
  'jquery',
  'underscore',
  'backbone',
  'models/server'
], function($, _, Backbone, ServerModel) {
  'use strict';
  var ServerCollection = Backbone.Collection.extend({
    model: ServerModel,
    initialize: function() {
      this.page = window.server_page || 0;
    },
    url: function() {
      return '/server';
    },
    parse: function(response) {
      if (response.page !== undefined) {
        this.setPage(response.page);
        this.setPageTotal(response.page_total);
        return response.servers;
      }

      return response;
    },
    setPage: function(page) {
      this.page = page;
      window.server_page = page;
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
    isLastPage: function() {
      return this.page === this.pageTotal;
    }
  });

  return ServerCollection;
});
