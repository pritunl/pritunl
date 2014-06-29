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
  'views/modalDeleteUsers',
  'views/modalEmailUsers',
  'text!templates/orgsList.html'
], function($, _, Backbone, OrgCollection, UserCollection, ListView,
    OrgsListItemView, AlertView, ModalAddOrgView, ModalAddUserView,
    ModalDeleteUsersView, ModalEmailUsersView, orgsListTemplate) {
  'use strict';
  var OrgsListView = ListView.extend({
    listContainer: '.orgs-list-container',
    template: _.template(orgsListTemplate),
    listErrorMsg: 'Failed to load organizations, server error occurred.',
    events: {
      'click .orgs-add-org': 'onAddOrg',
      'click .orgs-add-user': 'onAddUser',
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
    onAddOrg: function() {
      var modal = new ModalAddOrgView();
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'warning',
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
          type: 'warning',
          message: 'Successfully added user.',
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
          type: 'warning',
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
    resetItems: function(views) {
      if (!views.length) {
        this.$('.orgs-add-user').attr('disabled', 'disabled');
        this.$('.no-orgs').slideDown(250);
      }
      else {
        this.$('.orgs-add-user').removeAttr('disabled');
        this.$('.no-orgs').slideUp(250);
      }
    }
  });

  return OrgsListView;
});
