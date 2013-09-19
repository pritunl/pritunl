define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var ListView = Backbone.View.extend({
    listContainer: null,
    initialize: function(options) {
      this.init(options);
      this.listenTo(this.collection, 'reset', this._onReset);
      this.views = [];
    },
    init: function() {
    },
    render: function() {
      this.$el.html(this.template());
      this.update();
      return this;
    },
    _removeItemSlide: function(view) {
      view.$el.slideUp({
        duration: 250,
        complete: function() {
          this.removeItem(view);
        }.bind(this)
      });
    },
    _onReset: function(collection) {
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
          this._removeItemSlide(this.views[i]);
          this.views.splice(i, 1);
          i -= 1;
        }
      }

      // Add new elements
      for (i = 0; i < collection.models.length; i++) {
        if (currentModels.indexOf(collection.models[i].get('id')) !== -1) {
          continue;
        }

        modelView = this.buildItem(collection.models[i]);
        this.addView(modelView);
        this.views.splice(i, 0, modelView);
        modelView.render().$el.hide();

        if (i === 0) {
          if (this.listContainer) {
            this.$(this.listContainer).prepend(modelView.el);
          }
          else {
            this.$el.prepend(modelView.el);
          }
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
        this.views[i].update();
      }

      this.resetItems(this.views);
    },
    update: function() {
      this.collection.fetch({
        reset: true,
        error: function() {
          this.collection.reset();
        }.bind(this)
      });
    },
    removeItem: function(view) {
      view.destroy();
    },
    buildItem: function() {
    },
    resetItems: function() {
    }
  });

  return ListView;
});
