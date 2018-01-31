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
      this.link = options.link;
      this.listenTo(window.events, 'links_updated', this.update);
      this.interval = setInterval((this.update).bind(this), 2000);
      LinkLocationsListView.__super__.initialize.call(this);
    },
    deinitialize: function() {
      clearInterval(this.interval);
    },
    buildItem: function(model) {
      return new LinkLocationsListItemView({
        model: model,
        collection: this.collection,
        link: this.link
      });
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
