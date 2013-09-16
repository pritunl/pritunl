define([
  'jquery',
  'underscore',
  'backbone',
  'collections/org',
  'collections/user',
  'views/orgsListItem',
  'views/alert',
  'views/modalAddOrg',
  'views/modalAddUser',
  'views/modalDeleteUsers',
  'text!templates/orgsList.html'
], function($, _, Backbone, OrgCollection, UserCollection,
    OrgsListItemView, AlertView, ModalAddOrgView, ModalAddUserView,
    ModalDeleteUsersView, orgsListTemplate) {
  'use strict';
  var OrgsListView = Backbone.View.extend({
    template: _.template(orgsListTemplate),
    events: {
      'click .orgs-add-org': 'onAddOrg',
      'click .orgs-add-user': 'onAddUser',
      'click .orgs-del-selected': 'onDelSelected'
    },
    initialize: function() {
      this.collection = new OrgCollection();
      this.listenTo(this.collection, 'reset', this.onReset);
      this.views = [];
      this.selected = [];
    },
    render: function() {
      this.$el.html(this.template());
      this.collection.reset([
        {
          'id': '7ea4e93cb44b4db5ae5322105363677f',
          'name': 'organizationname1'
        },
        {
          'id': 'f069f8e7566c47f99b72420252d42a4b',
          'name': 'organizationname2'
        },
        {
          'id': 'e29dd434c59f4b07b19efc1dbdfaff31',
          'name': 'organizationname3'
        }
      ]);
      return this;
    },
    removeItem: function(view) {
      view.$el.slideUp({
        duration: 250,
        complete: function() {
          view.remove();
        }.bind(this)
      });
    },
    onAddOrg: function() {
      var modal = new ModalAddOrgView();
    },
    onAddUser: function() {
      var modal = new ModalAddUserView({
        orgs: this.collection
      });
    },
    onDelSelected: function(view) {
      var i;
      var models = [];

      for (i = 0; i < this.selected.length; i++) {
        models.push(this.selected[i].model);
      }

      var modal = new ModalDeleteUsersView({
        users: new UserCollection(models)
      });
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
        this.$('.orgs-del-selected').removeAttr('disabled');
      }
      else {
        this.$('.orgs-del-selected').attr('disabled', 'disabled');
      }
    },
    onReset: function(collection) {
      var i;
      var modelView;
      var attr;
      var modified;
      var currentModels = [];
      var newModels = [];

      for (i = 0; i < this.views.length; i++) {
        currentModels.push(this.views[i].model.get('id'));
      }

      for (i = 0; i < collection.models.length; i++) {
        newModels.push(collection.models[i].get('id'));
      }

      // Remove elements that no longer exists
      for (i = 0; i < this.views.length; i++) {
        if (newModels.indexOf(this.views[i].model.get('id')) === -1) {
          // Remove item from dom and array
          this.removeItem(this.views[i]);
          this.views.splice(i, 1);
          i -= 1;
        }
      }

      // Add new elements
      for (i = 0; i < collection.models.length; i++) {
        if (currentModels.indexOf(collection.models[i].get('id')) !== -1) {
          continue;
        }

        modelView = new OrgsListItemView({model: collection.models[i]});
        this.views.splice(i, 0, modelView);
        this.listenTo(modelView, 'select', this.onSelect);
        modelView.render().$el.hide();

        if (i === 0) {
          this.$('.orgs-list-container').prepend(modelView.el);
        }
        else {
          this.views[i - 1].$el.after(modelView.el);
        }

        modelView.$el.slideDown(250);
      }

      // Check for modified data
      for (i = 0; i < collection.models.length; i++) {
        modified = false;

        // Check each attr for modified data
        for (attr in collection.models[i].attributes) {
          if (collection.models[i].get(attr) !==
              this.views[i].model.get(attr)) {
            modified = true;
            break;
          }
        }

        if (!modified) {
          continue;
        }

        // If data was modified updated attributes and render
        this.views[i].model.set(collection.models[i].attributes);
        this.views[i].render();
      }

      if (!this.views.length) {
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
