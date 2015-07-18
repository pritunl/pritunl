define([
  'jquery',
  'underscore',
  'backbone',
  'models/org'
], function($, _, Backbone, OrgModel) {
  'use strict';
  var OrgCollection = Backbone.Collection.extend({
    model: OrgModel,
    initialize: function() {
      this.page = window.org_page || 0;
    },
    url: function() {
      return '/organization';
    },
    parse: function(response) {
      if (response.page !== undefined) {
        this.setPage(response.page);
        this.setPageTotal(response.page_total);
        return response.organizations;
      }

      return response;
    },
    setPage: function(page) {
      this.page = page;
      window.org_page = page;
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

  return OrgCollection;
});
