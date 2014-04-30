define([
  'jquery',
  'underscore',
  'backbone',
  'views/alert'
], function($, _, Backbone, AlertView) {
  'use strict';
  // Max number of views to use slide animation on reset
  var MAX_SLIDE_COUNT = 5;

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
    _showItem: function(view, slide, complete) {
      view.visible = true;
      if (slide === false) {
        view.$el.show();
        if (complete) {
          complete(view);
        }
      }
      else {
        view.$el.slideDown({
          duration: 250,
          complete: function() {
            if (complete) {
              complete(view);
            }
          }
        });
      }
    },
    _hideItem: function(view, slide, complete) {
      view.visible = false;
      if (slide === false) {
        view.$el.hide();
        if (complete) {
          complete(view);
        }
      }
      else {
        view.$el.slideUp({
          duration: 250,
          complete: function() {
            if (complete) {
              complete(view);
            }
          }
        });
      }
    },
    _removeItem: function(view, slide) {
      this._hideItem(view, slide, (this.removeItem).bind(this));
    },
    _onReset: function(collection, options) {
      if (this.ignore(options)) {
        return;
      }
      var i;
      var newIndex;
      var modelView;
      var currentModels = [];
      var newModels = [];
      // Num of views currently visible
      var curVisible = 0;
      // Num of views that will be visible
      var newVisible = 0;
      // Num of views that will be removed
      var delTotal = 0;
      // Num of views that will be added
      var addTotal = 0;
      // Num of views that will be removed with slide animation
      var delSlide;
      // Num of views that will be added with slide animation
      var addSlide;
      // Num of view removes to pass before removing with slide animation
      var passDel;
      // Num of view adds to pass before adding with slide animation
      var passAdd;
      // Number of views that have been removed with slide animation
      var delSlideCount = 0;
      // Number of views that have been added with slide animation
      var addSlideCount = 0;
      // Number of view adds that have been passed without slide animation
      var passDelCount = 0;
      // Number of view removes that have been passed without slide animation
      var passAddCount = 0;
      var slide = this.views.length ? true : false;
      var scroll = $(document).scrollTop();

      for (i = 0; i < collection.models.length; i++) {
        newModels.push(collection.models[i].get('id'));
      }

      for (i = 0; i < this.views.length; i++) {
        currentModels.push(this.views[i].model.get('id'));
      }

      for (i = 0; i < this.views.length; i++) {
        if (this.views[i].visible) {
          curVisible += 1;
          if (newModels.indexOf(this.views[i].model.get('id')) === -1 ||
              (this.views[i].model.get('hidden') && !this.showHidden)) {
            delTotal += 1;
          }
        }
      }

      for (i = 0; i < collection.models.length; i++) {
        if (!collection.models[i].get('hidden') || this.showHidden) {
          newVisible += 1;
        }
        if (currentModels.indexOf(collection.models[i].get('id')) !== -1) {
          continue;
        }
        if (!collection.models[i].get('hidden') || this.showHidden) {
          addTotal += 1;
        }
      }

      // Calculate the number of views that will be added/removed with
      // slide animation and the number of add/removes that will be
      // passed without slide animation
      // End result is showing a slide animation only for new and removed
      // item slots. So if the current colection has 5 elements and the new
      // collection has 10 new different elements. There will be no slide
      // animation when removing the current 5 elements and no slide
      // animation when adding the first 5 new elements. After the existing
      // and new 5 elements are added and removed the next 5 new elements
      // will have a slide animation
      delSlide = Math.max(0, curVisible - newVisible);
      addSlide = Math.max(0, newVisible - curVisible);
      passDel = 0;
      if (delSlide) {
        passDel = Math.max(0, delTotal - delSlide);
      }
      passAdd = 0;
      if (addSlide) {
        passAdd = Math.max(0, addTotal - addSlide);
      }
      delSlide = Math.min(MAX_SLIDE_COUNT, delSlide);
      addSlide = Math.min(MAX_SLIDE_COUNT, addSlide);

      // Remove elements that no longer exists
      for (i = 0; i < this.views.length; i++) {
        if (newModels.indexOf(this.views[i].model.get('id')) === -1) {
          // Remove item from dom and array
          if (!slide || delSlideCount >= delSlide || passDelCount < passDel) {
            this._removeItem(this.views[i], false);
            passDelCount += 1;
          }
          else {
            this._removeItem(this.views[i], true);
            delSlideCount += 1;
          }
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

        if (!modelView.model.get('hidden') || this.showHidden) {
          if (!slide || addSlideCount >= addSlide || passAddCount < passAdd) {
            this._showItem(modelView, false);
            passAddCount += 1;
          }
          else {
            this._showItem(modelView, true);
            addSlideCount += 1;
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
        // Check each attr for modified data
        if (!this.isItemChanged(this.views[i].model, collection.models[i])) {
          continue;
        }

        // If data was modified updated attributes and render
        this.views[i].model.set(collection.models[i].attributes);
        this.views[i].update();
      }

      var views = [];
      for (i = 0; i < this.views.length; i++) {
        if (this.views[i].model.get('hidden')) {
          if (this.showHidden) {
            if (addSlideCount >= addSlide || passAddCount < passAdd) {
              this._showItem(this.views[i], false);
              passAddCount += 1;
            }
            else {
              this._showItem(this.views[i], true);
              addSlideCount += 1;
            }
          }
          else {
            if (delSlideCount >= delSlide || passDelCount < passDel) {
              this._hideItem(this.views[i], false);
              passDelCount += 1;
            }
            else {
              this._hideItem(this.views[i], true);
              delSlideCount += 1;
            }
            continue;
          }
        }
        views.push(this.views[i]);
      }
      this.resetItems(views);
      $(document).scrollTop(scroll);
    },
    update: function() {
      var loading = true;

      setTimeout(function() {
        if (!loading) {
          return;
        }
        this.loading = false;
        this.$('.loading').slideDown(250);
      }.bind(this), 400);

      this.collection.fetch({
        data: this.getOptions(),
        reset: true,
        error: function() {
          loading = false;
          this.$('.loading').slideUp(250);
          var alertView = new AlertView({
            type: 'danger',
            message: this.listErrorMsg,
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
          this.collection.reset();
        }.bind(this),
        success: function() {
          loading = false;
          this.$('.loading').slideUp(250);
        }.bind(this)
      });
    },
    ignore: function() {
    },
    getOptions: function() {
    },
    removeItem: function(view) {
      view.destroy();
    },
    buildItem: function() {
    },
    resetItems: function() {
    },
    isItemChanged: function(model, newModel) {
      var attr;
      for (attr in newModel.attributes) {
        if (model.get(attr) !== newModel.get(attr)) {
          return true;
        }
      }
      return false;
    }
  });

  return ListView;
});
