define([
  'jquery',
  'underscore',
  'backbone',
  'collections/org',
  'collections/user',
  'views/list',
  'views/orgsListItem',
  'views/alert',
  'views/modalAddOrg',
  'views/modalAddUser',
  'views/modalAddUserBulk',
  'views/modalDeleteUsers',
  'views/modalEmailUsers',
  'text!templates/orgsList.html'
], function($, _, Backbone, OrgCollection, UserCollection, ListView,
    OrgsListItemView, AlertView, ModalAddOrgView, ModalAddUserView,
    ModalAddUserBulkView, ModalDeleteUsersView, ModalEmailUsersView,
    orgsListTemplate) {
  'use strict';
  var OrgsListView = ListView.extend({
    listContainer: '.orgs-list-container',
    template: _.template(orgsListTemplate),
    listErrorMsg: 'Failed to load organizations, server error occurred.',
    events: {
      'click .orgs-list > .prev-page': 'prevPage',
      'click .orgs-list > .next-page': 'nextPage',
      'click .orgs-list > .pages .link.first': 'firstPage',
      'click .orgs-list > .pages .link.last': 'lastPage',
      'click .orgs-add-org': 'onAddOrg',
      'click .orgs-add-user': 'onAddUser',
      'click .orgs-add-user-bulk': 'onAddUserBulk',
      'click .orgs-del-selected': 'onDelSelected',
      'click .orgs-email-selected': 'onEmailSelected'
    },
    initialize: function() {
      this.collection = new OrgCollection();
      this.listenTo(window.events, 'organizations_updated', this.update);
      this.selected = [];
      OrgsListView.__super__.initialize.call(this);
    },
    removeItem: function(view) {
      var i;
      var views = view.usersListView.views;
      for (i = 0; i < views.length; i++) {
        if (views[i].getSelect()) {
          views[i].setSelect(false);
        }
      }
      view.destroy();
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
    onAddOrg: function() {
      var modal = new ModalAddOrgView();
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully added organization.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    onAddUser: function() {
      var modal = new ModalAddUserView({
        orgs: this.collection
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully added user.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    onAddUserBulk: function() {
      var modal = new ModalAddUserBulkView({
        orgs: this.collection
      });
      this.listenToOnce(modal, 'applied', function(response) {
        var msg;

        if (response) {
          msg = response;
        } else {
          msg = 'Successfully added users.';
        }

        var alertView = new AlertView({
          type: 'success',
          message: msg,
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    onDelSelected: function() {
      var i;
      var models = [];

      for (i = 0; i < this.selected.length; i++) {
        models.push(this.selected[i].model);
      }

      var modal = new ModalDeleteUsersView({
        collection: new UserCollection(models)
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully deleted selected users.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    onEmailSelected: function() {
      var i;
      var models = [];

      for (i = 0; i < this.selected.length; i++) {
        models.push(this.selected[i].model);
      }

      var modal = new ModalEmailUsersView({
        collection: new UserCollection(models)
      });
      this.addView(modal);
    },
    onSelect: function(view) {
      var i;

      if (view.getSelect()) {
        this.selected.push(view);
      }
      else {
        for (i = 0; i < this.selected.length; i++) {
          if (this.selected[i] === view) {
            this.selected.splice(i, 1);
          }
        }
      }

      if (this.selected.length) {
        this.$('.orgs-email-selected, .orgs-del-selected').removeAttr(
          'disabled');
      }
      else {
        this.$('.orgs-email-selected, .orgs-del-selected').attr(
          'disabled', 'disabled');
      }
    },
    buildItem: function(model) {
      var modelView = new OrgsListItemView({
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
      this.$('.orgs-list > .pages .link.last').before(pageElem);
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
        this.$('.orgs-add-user').attr('disabled', 'disabled');
        this.$('.orgs-add-user-bulk').attr('disabled', 'disabled');
        this.$('.no-orgs').slideDown(window.slideTime);
      }
      else {
        this.$('.orgs-add-user').removeAttr('disabled');
        this.$('.orgs-add-user-bulk').removeAttr('disabled');
        this.$('.no-orgs').slideUp(window.slideTime);
      }

      if (!this.collection.getPage()) {
        this.$('.orgs-list > .pages').addClass('padded-left');
        this.$('.prev-page').hide();
      }
      else {
        this.$('.orgs-list > .pages').removeClass('padded-left');
        this.$('.orgs-list > .prev-page').show();
      }
      if (this.collection.isLastPage()) {
        this.$('.orgs-list > .pages').addClass('padded-right');
        this.$('.orgs-list > .next-page').hide();
      }
      else {
        this.$('.orgs-list > .pages').removeClass('padded-right');
        this.$('.orgs-list > .next-page').show();
      }

      if (pageTotal < 2) {
        this.$('.orgs-list > .pages').hide();
      }
      else{
        this.$('.orgs-list > .pages').show();
        var i;
        var page = Math.max(0, curPage - 7);
        this.$('.orgs-list > .pages .link.page').remove();
        this.$('.orgs-list > .pages .link.first').removeClass('current');
        this.$('.orgs-list > .pages .link.last').removeClass('current');
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
          this.$('.orgs-list > .pages .link.first').addClass('current');
        }
        else if (curPage === pageTotal) {
          this.$('.orgs-list > .pages .link.last').addClass('current');
        }
      }
    }
  });

  return OrgsListView;
});
