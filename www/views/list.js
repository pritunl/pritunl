define([
  'jquery',
  'underscore',
  'backbone',
  'views/alert'
], function($, _, Backbone, AlertView) {
  'use strict';
  var ListView = Backbone.View.extend({
    listContainer: null,
    listErrorMsg: 'Failed to load list, server error occurred.',
    initialize: function() {
      this.listenTo(this.collection, 'reset', this._onReset);
      this.views = [];
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
      var newIndex;
      var modelView;
      var attr;
      var modified;
      var currentModels = [];
      var newModels = [];
      var empty = this.views.length ? false : true;

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

        if (!modelView.hidden || this.showHidden) {
          if (empty) {
            modelView.$el.show();
          }
          else {
            modelView.$el.slideDown(250);
          }
        }
      }

      // Update current models
      currentModels = [];
      for (i = 0; i < this.views.length; i++) {
        currentModels.push(this.views[i].model.get('id'));
      }

      // Check for unsorted elements with insertion sort
      while (true) {
        for (i = 0; i < currentModels.length; i++) {
          newIndex = newModels.indexOf(currentModels[i]);

          if (newIndex < i) {
            if (newIndex === 0) {
              if (this.listContainer) {
                this.$(this.listContainer).prepend(this.views[i].el);
              }
              else {
                this.$el.prepend(this.views[i].el);
              }
            }
            else {
              this.views[newIndex - 1].$el.after(this.views[i].el);
            }

            this.views.splice(newIndex, 0, this.views.splice(i, 1)[0]);
            currentModels.splice(newIndex, 0, currentModels.splice(i, 1)[0]);
            break;
          }
        }

        if (i === currentModels.length) {
          break;
        }
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

      var views = [];
      for (i = 0; i < this.views.length; i++) {
        if (this.views[i].hidden) {
          if (this.showHidden) {
            this.views[i].$el.slideDown(250);
          }
          else {
            this.views[i].$el.slideUp(250);
            continue;
          }
        }
        views.push(this.views[i]);
      }
      this.resetItems(views);
    },
    update: function() {
      this.collection.fetch({
        reset: true,
        error: function() {
          var alertView = new AlertView({
            type: 'danger',
            message: this.listErrorMsg,
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
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
