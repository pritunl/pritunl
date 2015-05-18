define([
  'jquery',
  'underscore',
  'backbone',
  'collections/host',
  'views/list',
  'views/alert',
  'views/hostsListItem',
  'text!templates/hostsList.html'
], function($, _, Backbone, HostCollection, ListView, AlertView,
    HostsListItemView, hostsListTemplate) {
  'use strict';
  var HostsListView = ListView.extend({
    className: 'hosts-list',
    listContainer: '.hosts-list-container',
    template: _.template(hostsListTemplate),
    listErrorMsg: 'Failed to load hosts, server error occurred.',
    events: {
      'click .prev-page': 'prevPage',
      'click .next-page': 'nextPage',
      'click .link.first': 'firstPage',
      'click .link.last': 'lastPage'
    },
    initialize: function() {
      this.collection = new HostCollection();
      this.listenTo(window.events, 'hosts_updated', this.update);
      HostsListView.__super__.initialize.call(this);
    },
    prevPage: function() {
      this.collection.prevPage();
      this.update();
    },
    nextPage: function() {
      this.collection.nextPage();
      this.update();
    },
    firstPage: function() {
      this.collection.setPage(0);
      this.update();
    },
    lastPage: function() {
      this.collection.setPage(this.collection.getPageTotal());
      this.update();
    },
    buildItem: function(model) {
      var modelView = new HostsListItemView({
        model: model
      });
      this.listenTo(modelView, 'select', this.onSelect);
      return modelView;
    },
    getOptions: function() {
      return {
        'page': this.collection.getPage()
      };
    },
    addPageElem: function(page, curPage) {
      var pageElem = $('<a class="link page">' + (page + 1) + '</a>');
      this.$('.pages .link.last').before(pageElem);
      if (page === curPage) {
        pageElem.addClass('current');
      }
      pageElem.one('click', function() {
        this.collection.setPage(page);
        this.update();
      }.bind(this));
    },
    resetItems: function(views) {
      var curPage = this.collection.getPage();
      var pageTotal = this.collection.getPageTotal();

      if (!views.length) {
        this.$('.servers-attach-org').attr('disabled', 'disabled');
        this.$('.no-servers').slideDown(window.slideTime);
      }
      else {
        this.$('.servers-attach-org').removeAttr('disabled');
        this.$('.no-servers').slideUp(window.slideTime);
      }

      if (!this.collection.getPage()) {
        this.$('.pages').addClass('padded-left');
        this.$('.prev-page').hide();
      }
      else {
        this.$('.pages').removeClass('padded-left');
        this.$('.prev-page').show();
      }
      if (this.collection.isLastPage()) {
        this.$('.pages').addClass('padded-right');
        this.$('.next-page').hide();
      }
      else {
        this.$('.pages').removeClass('padded-right');
        this.$('.next-page').show();
      }

      if (pageTotal < 2) {
        this.$('.pages').hide();
      }
      else{
        this.$('.pages').show();
        var i;
        var page = Math.max(0, curPage - 7);
        this.$('.pages .link.page').remove();
        this.$('.pages .link.first').removeClass('current');
        this.$('.pages .link.last').removeClass('current');
        for (i = 0; i < 15; i++) {
          if (page > 0) {
            this.addPageElem(page, curPage);
          }
          page += 1;
          if (page > pageTotal - 1) {
            break;
          }
        }
        if (curPage === 0) {
          this.$('.pages .link.first').addClass('current');
        }
        else if (curPage === pageTotal) {
          this.$('.pages .link.last').addClass('current');
        }
      }
    }
  });

  return HostsListView;
});
