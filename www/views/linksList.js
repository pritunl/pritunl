define([
  'jquery',
  'underscore',
  'backbone',
  'collections/link',
  'views/list',
  'views/alert',
  'views/linksListItem',
  'views/modalAddLink',
  'views/modalAddLocation',
  'text!templates/linksList.html'
], function($, _, Backbone, LinkCollection, ListView, AlertView,
    LinksListItemView, ModalAddLinkView, ModalAddLocationView,
    linksListTemplate) {
  'use strict';
  var LinksListView = ListView.extend({
    listContainer: '.links-list-container',
    template: _.template(linksListTemplate),
    listErrorMsg: 'Failed to load links, server error occurred.',
    events: {
      'click .links-add-link': 'onAddLink',
      'click .links-add-location': 'onAddLocation',
      'click .links-list > .prev-page': 'prevPage',
      'click .links-list > .next-page': 'nextPage',
      'click .links-list > .pages .page-link.first': 'firstPage',
      'click .links-list > .pages .page-link.last': 'lastPage'
    },
    initialize: function() {
      this.collection = new LinkCollection();
      this.listenTo(window.events, 'links_updated', this.update);
      LinksListView.__super__.initialize.call(this);
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
    onAddLink: function() {
      var modal = new ModalAddLinkView();
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully added link.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    onAddLocation: function() {
      var modal = new ModalAddLocationView({
        links: this.collection
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully added location.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    buildItem: function(model) {
      var modelView = new LinksListItemView({
        model: model
      });
      return modelView;
    },
    getOptions: function() {
      return {
        'page': this.collection.getPage()
      };
    },
    addPageElem: function(page, curPage) {
      var pageElem = $('<a class="page-link page">' + (page + 1) + '</a>');
      this.$('.links-list > .pages .page-link.last').before(pageElem);
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
        this.$('.links-add-location').attr('disabled', 'disabled');
        this.$('.links-add-route').attr('disabled', 'disabled');
        this.$('.no-links').slideDown(window.slideTime);
      }
      else {
        this.$('.links-add-location').removeAttr('disabled');
        this.$('.links-add-route').removeAttr('disabled');
        this.$('.no-links').slideUp(window.slideTime);
      }

      if (!this.collection.getPage()) {
        this.$('.links-list > .pages').addClass('padded-left');
        this.$('.prev-page').hide();
      }
      else {
        this.$('.links-list > .pages').removeClass('padded-left');
        this.$('.links-list > .prev-page').show();
      }
      if (this.collection.isLastPage()) {
        this.$('.links-list > .pages').addClass('padded-right');
        this.$('.links-list > .next-page').hide();
      }
      else {
        this.$('.links-list > .pages').removeClass('padded-right');
        this.$('.links-list > .next-page').show();
      }

      if (pageTotal < 2) {
        this.$('.links-list > .pages').hide();
      }
      else{
        this.$('.links-list > .pages').show();
        var i;
        var page = Math.max(0, curPage - 7);
        this.$('.links-list > .pages .page-link.page').remove();
        this.$('.links-list > .pages .page-link.first').removeClass('current');
        this.$('.links-list > .pages .page-link.last').removeClass('current');
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
          this.$('.links-list > .pages .page-link.first').addClass('current');
        }
        else if (curPage === pageTotal) {
          this.$('.links-list > .pages .page-link.last').addClass('current');
        }
      }
    }
  });

  return LinksListView;
});
