define([
  'jquery',
  'underscore',
  'backbone',
  'models/link'
], function($, _, Backbone, LinkModel) {
  'use strict';
  var LinkCollection = Backbone.Collection.extend({
    model: LinkModel,
    initialize: function() {
      this.page = window.link_page || 0;
    },
    url: function() {
      return '/link';
    },
    parse: function(response) {
      if (response.page !== undefined) {
        this.setPage(response.page);
        this.setPageTotal(response.page_total);
        return response.links;
      }

      return response;
    },
    setPage: function(page) {
      this.page = page;
      window.link_page = page;
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

  return LinkCollection;
});
