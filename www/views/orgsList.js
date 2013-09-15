define([
  'jquery',
  'underscore',
  'backbone',
  'collections/org',
  'views/orgsListItem',
  'views/alert',
  'text!templates/orgsList.html'
], function($, _, Backbone, OrgCollection, OrgsListItemView, AlertView,
    orgsListTemplate) {
  'use strict';
  var OrgsListView = Backbone.View.extend({
    template: _.template(orgsListTemplate),
    events: {
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
    onDelSelected: function(view) {
      var i;

      for (i = 0; i < this.selected.length; i++) {
        this.removeItem(this.selected[i]);
      }

      new AlertView({
        type: 'warning',
        message: 'Successfully deleted selected users.'
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
    }
  });

  return OrgsListView;
});
