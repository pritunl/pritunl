define([
  'jquery',
  'underscore',
  'backbone',
  'collections/log',
  'views/dashboardLogItem',
  'text!templates/dashboardLog.html'
], function($, _, Backbone, LogCollection, DashboardLogItemView,
    dashboardLogTemplate) {
  'use strict';
  var DashboardLogView = Backbone.View.extend({
    className: 'log-container',
    template: _.template(dashboardLogTemplate),
    initialize: function() {
      this.collection = new LogCollection();
      this.listenTo(this.collection, 'reset', this.onReset);
      this.views = [];
    },
    render: function() {
      this.$el.html(this.template());
      this.collection.reset([
        {
          'id': 'd5d860c2a5af48e2933e42119be5f43c',
          'date': '03:57 pm - Sep 15, 2013',
          'message': 'Deleted users.'
        },
        {
          'id': '8d7701a94bd74facb49f9e17fee167a7',
          'date': '03:45 pm - Sep 15, 2013',
          'message': 'Created new user.'
        },
        {
          'id': '47215fea69984943a495ae753aa30d0e',
          'date': '03:42 pm - Sep 15, 2013',
          'message': 'Created new user.'
        },
        {
          'id': 'd4f574b8a8ac492e9567701b3f2e61a4',
          'date': '03:38 pm - Sep 15, 2013',
          'message': 'Deleted users.'
        },
        {
          'id': '862a2e45265f41b296e2b5398a7c0456',
          'date': '03:35 pm - Sep 15, 2013',
          'message': 'Created new user.'
        },
        {
          'id': 'b71c8e01d59541bda2e8efb4a5cccffc',
          'date': '03:32 pm - Sep 15, 2013',
          'message': 'Deleted users.'
        },
        {
          'id': '3dcae23770414aceaecc8a496d499aa8',
          'date': '03:23 pm - Sep 15, 2013',
          'message': 'Created new user.'
        },
        {
          'id': 'a8df39ca6e2d4ebe8e538dc4a6fa5a96',
          'date': '03:14 pm - Sep 15, 2013',
          'message': 'Deleted users.'
        },
        {
          'id': '2b97bbf1f7914444bdb0f20c2b6c1364',
          'date': '03:11 pm - Sep 15, 2013',
          'message': 'Created new user.'
        },
        {
          'id': '89436addc66442bf8604dc45fe2eaf0f',
          'date': '03:03 pm - Sep 15, 2013',
          'message': 'Created new organization.'
        }
      ]);
      return this;
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

        modelView = new DashboardLogItemView({
          model: collection.models[i]
        });
        this.addView(modelView);
        this.views.splice(i, 0, modelView);
        this.listenTo(modelView, 'select', this.onSelect);
        modelView.render().$el.hide();

        if (i === 0) {
          this.$('.log-entry-list').prepend(modelView.el);
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

      if (this.views.length) {
        this.$('.last').removeClass('last');
        this.views[this.views.length - 1].$el.addClass('last');
      }

    }
  });

  return DashboardLogView;
});
