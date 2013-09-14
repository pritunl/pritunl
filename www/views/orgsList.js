define([
  'jquery',
  'underscore',
  'backbone',
  'collections/org',
  'text!templates/orgsList.html'
], function($, _, Backbone, OrgCollection,
    orgsListTemplate) {
  'use strict';
  var OrgsListView = Backbone.View.extend({
    template: _.template(orgsListTemplate),
    render: function() {
      this.$el.html(this.template());
      return this;
    }
  });

  return OrgsListView;
});
