define([
  'jquery',
  'underscore',
  'backbone',
  'collections/linkLocation',
  'views/list',
  'views/linkLocationsListItem',
  'text!templates/linkLocationsList.html'
], function($, _, Backbone, LinkLocationCollection, ListView,
    LinkLocationsListItemView, linkLocationsListTemplate) {
  'use strict';
  var LinkLocationsListView = ListView.extend({
    className: 'link-locations-list',
    template: _.template(linkLocationsListTemplate),
    listErrorMsg: 'Failed to load link locations, ' +
      'server error occurred.',
    initialize: function(options) {
      this.collection = new LinkLocationCollection({
        link: options.link.get('id')
      });
      this.listenTo(window.events, 'link_locations_updated:' +
        options.link.get('id'), this.update);
      this.link = options.link;
      LinkLocationsListView.__super__.initialize.call(this);
    },
    buildItem: function(model) {
      var modelView = new LinkLocationsListItemView({
        model: model,
        link: this.link
      });
      return modelView;
    },
    resetItems: function(views) {
      if (!views.length) {
        this.$('.no-locations').slideDown(window.slideTime);
      }
      else {
        this.$('.no-locations').slideUp(window.slideTime);
      }
    }
  });

  return LinkLocationsListView;
});
