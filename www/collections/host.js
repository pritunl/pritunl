define([
  'jquery',
  'underscore',
  'backbone',
  'models/host'
], function($, _, Backbone, HostModel) {
  'use strict';
  var HostCollection = Backbone.Collection.extend({
    model: HostModel,
    initialize: function() {
      this.page = window.host_page || 0;
    },
    url: function() {
      return '/host';
    },
    parse: function(response) {
      if (response.page !== undefined) {
        this.setPage(response.page);
        this.setPageTotal(response.page_total);
        return response.hosts;
      }

      return response;
    },
    setPage: function(page) {
      this.page = page;
      window.host_page = page;
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

  return HostCollection;
});
