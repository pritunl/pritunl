define([
  'jquery',
  'underscore',
  'backbone',
  'collections/serverOrg',
  'views/list',
  'views/serverOrgsListItem',
  'text!templates/serverOrgsList.html'
], function($, _, Backbone, ServerOrgCollection, ListView,
    ServerOrgsListItemView, serverOrgsListTemplate) {
  'use strict';
  var ServerOrgsListView = ListView.extend({
    className: 'server-orgs-list',
    template: _.template(serverOrgsListTemplate),
    init: function(options) {
      this.collection = new ServerOrgCollection({
        server: options.server
      });
    },
    update: function() {
      this.collection.reset([
        {
          'id': '1',
          'server': '1',
          'name': 'testorg0',
        },
        {
          'id': '2',
          'server': '1',
          'name': 'testorg1',
        }
      ]);
    },
    buildItem: function(model) {
      var modelView = new ServerOrgsListItemView({
        model: model
      });
      return modelView;
    },
    resetItems: function(views) {
      if (!views.length) {
        this.$('.no-orgs').slideDown(250);
      }
      else {
        this.$('.no-orgs').slideUp(250);
      }
    }
  });

  return ServerOrgsListView;
});
