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
    listErrorMsg: 'Failed to load server organizations, ' +
      'server error occurred.',
    initialize: function(options) {
      this.collection = new ServerOrgCollection({
        server: options.server
      });
      this.listenTo(window.events, 'servers_updated', this.update);
      ServerOrgsListView.__super__.initialize.call(this);
    },
    update: function() {
      this.collection.reset([
        {
          'id': 'a48f72fcb29d42b583ef32aa2bcad49d',
          'server': '2eca7aa7852f49fbbb737585141014f4',
          'name': 'testorg0',
        },
        {
          'id': 'b3b02c88a9a44ae3883707052f58bad3',
          'server': '13f695ff5f0c4d32afdbb4ff658d143e',
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
