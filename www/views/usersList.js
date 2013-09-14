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
    initialize: function() {
      this.collection = new UserCollection();
      this.listenTo(this.collection, 'reset', this.onReset);
      this.views = [];
      this.selected = [];
    },
    render: function() {
      this.$el.html(this.template());
      this.collection.reset([
        {
          'id': '0ebeed1612f24c2dbd5bf2efc51f9b61',
          'username': 'username0',
          'status': true
        },
        {
          'id': '9487991a880146eabfa1c253f90ba690',
          'username': 'username1',
          'status': true
        },
        {
          'id': '87865d89ff914bdfb365fab85622620c',
          'username': 'username2',
          'status': false
        },
        {
          'id': '58887df5d0684dc98573f79f8d916aac',
          'username': 'username3',
          'status': true
        },
        {
          'id': '3bfbab146dae46199f02f9391ff8e61c',
          'username': 'username4',
          'status': false
        },
        {
          'id': '0aed88706e73451bad0edf7490f5c07b',
          'username': 'username5',
          'status': true
        },
        {
          'id': '8f198417c7e74417b66186b7bfbf5478',
          'username': 'username6',
          'status': false
        },
        {
          'id': 'b5b6ed6ab3394a879ee966aa492a5073',
          'username': 'username7',
          'status': false
        },
        {
          'id': '73fbd092edb74e7cb7427458a7233efe',
          'username': 'username8',
          'status': false
        },
        {
          'id': '832a8b3ff7c740d990c3a85f2a4287ca',
          'username': 'username9',
          'status': true
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

        modelView = new UsersListItemView({model: collection.models[i]});
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
    }
  });

  return UsersListView;
});
