define([
  'jquery',
  'underscore',
  'backbone',
  'collections/user',
  'views/usersListItem',
  'text!templates/usersList.html'
], function($, _, Backbone, UserCollection, UsersListItemView,
    usersListTemplate) {
  'use strict';
  var UsersListView = Backbone.View.extend({
    template: _.template(usersListTemplate),
    initialize: function(options) {
      this.collection = new UserCollection({
        organization: options.organization
      });
      this.listenTo(this.collection, 'reset', this.onReset);
      this.views = [];
      this.selected = [];
    },
    render: function() {
      this.$el.html(this.template());
      this.collection.fetch({
        reset: true
      });
      return this;
    },
    removeItem: function(view) {
      view.$el.slideUp({
        duration: 250,
        complete: function() {
          if (view.getSelect()) {
            view.setSelect(false);
          }
          view.destroy();
        }.bind(this)
      });
    },
    onSelect: function(view) {
      this.trigger('select', view);
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

        modelView = new UsersListItemView({
          model: collection.models[i]
        });
        this.addView(modelView);
        this.views.splice(i, 0, modelView);
        this.listenTo(modelView, 'select', this.onSelect);
        modelView.render().$el.hide();

        if (i === 0) {
          this.$el.prepend(modelView.el);
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
        this.$('.no-users').slideDown(250);
      }
    }
  });

  return UsersListView;
});
