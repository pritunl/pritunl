define([
  'jquery',
  'underscore',
  'backbone',
  'collections/admin',
  'views/list',
  'views/adminsListItem',
  'text!templates/adminsList.html'
], function($, _, Backbone, AdminCollection, ListView, AdminsListItemView,
    adminsListTemplate) {
  'use strict';
  var AdminsListView = ListView.extend({
    className: 'admins-list-container',
    template: _.template(adminsListTemplate),
    listErrorMsg: 'Failed to load administrators, server error occurred.',
    initialize: function() {
      this.collection = new AdminCollection();
      this.listenTo(window.events, 'administrators_updated', this.update);
      AdminsListView.__super__.initialize.call(this);
    },
    removeItem: function(view) {
      if (view.getSelect()) {
        view.setSelect(false);
      }
      view.destroy();
    },
    onSelect: function(view, shiftKey) {
      var i;
      var curView;
      var select = false;
      var lastSelected = this.lastSelected;
      if (lastSelected && shiftKey && lastSelected.getSelect() &&
          lastSelected !== view) {
        for (i = 0; i < this.views.length; i++) {
          curView = this.views[i];

          if (!select && (curView === lastSelected || curView === view)) {
            select = true;
          }
          else if (select && (curView === lastSelected || curView === view)) {
            this.views[i].setSelect(true);
            break;
          }

          if (select) {
            this.views[i].setSelect(true);
          }
        }
      }
      this.trigger('select', view);
      this.lastSelected = view;
    },
    buildItem: function(model) {
      var modelView = new AdminsListItemView({
        model: model
      });
      this.listenTo(modelView, 'select', this.onSelect);
      return modelView;
    }
  });

  return AdminsListView;
});
