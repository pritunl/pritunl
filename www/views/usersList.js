define([
  'jquery',
  'underscore',
  'backbone',
  'collections/user',
  'views/list',
  'views/usersListItem',
  'text!templates/usersList.html'
], function($, _, Backbone, UserCollection, ListView, UsersListItemView,
    usersListTemplate) {
  'use strict';
  var UsersListView = ListView.extend({
    className: 'users-list-container',
    template: _.template(usersListTemplate),
    listErrorMsg: 'Failed to load users, server error occurred.',
    events: {
      'click .prev-page': 'prevPage',
      'click .next-page': 'nextPage',
      'click .link.first': 'firstPage',
      'click .link.last': 'lastPage'
    },
    initialize: function(options) {
      this.collection = new UserCollection({
        org: options.org
      });
      this.listenTo(window.events, 'users_updated:' +
        this.collection.org, this.update);
      UsersListView.__super__.initialize.call(this);
    },
    removeItem: function(view) {
      if (view.getSelect()) {
        view.setSelect(false);
      }
      view.destroy();
    },
    onSelect: function(view) {
      this.trigger('select', view);
    },
    buildItem: function(model) {
      var modelView = new UsersListItemView({
        model: model
      });
      this.listenTo(modelView, 'select', this.onSelect);
      return modelView;
    },
    resetItems: function(views) {
      if (!views.length) {
        this.$('.no-users').slideDown(250);
      }
      else {
        this.$('.no-users').slideUp(250);
      }
      if (this.collection.getSearch()) {
        this.$('.prev-page').hide();
        this.$('.next-page').hide();
        this.$('.pages').hide();
        this.$('.search-time').text('search processed in ' +
          this.collection.getSearchTime() + ' seconds')
        this.$('.search-time').show();
      }
      else {
        var curPage = this.collection.getPage();
        var pageTotal = this.collection.getPageTotal();

        this.$('.search-time').hide();
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
          var pageElem;
          this.$('.pages .link.page').remove();
          this.$('.pages .link.first').removeClass('current');
          this.$('.pages .link.last').removeClass('current');
          for (i = 0; i < 15; i++) {
            if (page > 0) {
              pageElem = $('<a class="link page">' + (page + 1) + '</a>');
              this.$('.pages .link.last').before(pageElem);
              if (page === curPage) {
                pageElem.addClass('current');
              }
              pageElem.one('click', function(evt) {
                var pageNum = parseInt($(evt.target).text()) - 1;
                this.collection.setPage(pageNum);
                this.update();
              }.bind(this));
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
    },
    getOptions: function() {
      if (this.collection.getSearch()) {
        return {
          'search': this.collection.getSearch()
        };
      }
      else {
        return {
          'page': this.collection.getPage()
        };
      }
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
    search: function(term) {
      this.collection.setSearch(term);
      this.update();
    }
  });

  return UsersListView;
});
