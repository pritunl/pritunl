define([
  'jquery',
  'underscore',
  'backbone',
  'collections/host',
  'views/list',
  'views/alert',
  'views/hostsListItem',
  'text!templates/hostsList.html'
], function($, _, Backbone, HostCollection, ListView, AlertView,
    HostsListItemView, hostsListTemplate) {
  'use strict';
  var HostsListView = ListView.extend({
    className: 'hosts-list',
    listContainer: '.hosts-list-container',
    template: _.template(hostsListTemplate),
    listErrorMsg: 'Failed to load hosts, server error occurred.',
    events: {},
    initialize: function() {
      this.collection = new HostCollection();
      this.listenTo(window.events, 'hosts_updated', this.update);
      HostsListView.__super__.initialize.call(this);
    },
    buildItem: function(model) {
      var modelView = new HostsListItemView({
        model: model
      });
      this.listenTo(modelView, 'select', this.onSelect);
      return modelView;
    },
    resetItems: function(views) {
      if (!views.length) {
        this.$('.servers-attach-org').attr('disabled', 'disabled');
        this.$('.no-servers').slideDown(window.slideTime);
      }
      else {
        this.$('.servers-attach-org').removeAttr('disabled');
        this.$('.no-servers').slideUp(window.slideTime);
      }
    }
  });

  return HostsListView;
});
