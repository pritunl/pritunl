define([
  'jquery',
  'underscore',
  'backbone',
  'views/alert',
  'views/usersList',
  'views/modalRenameOrg',
  'views/modalDeleteOrg',
  'text!templates/orgsListItem.html'
], function($, _, Backbone, AlertView, UsersListView, ModalRenameOrgView,
    ModalDeleteOrgView, orgsListItemTemplate) {
  'use strict';
  var OrgsListItemView = Backbone.View.extend({
    template: _.template(orgsListItemTemplate),
    events: {
      'click .org-rename': 'onRename',
      'click .org-del': 'onDelete',
      'click .download-key': 'onDownloadKey'
    },
    initialize: function() {
      this.usersListView = new UsersListView({
        organization: this.model.get('id')
      });
      this.listenTo(this.usersListView, 'select', this.onSelect);
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      this.$('.users-list-container').append(this.usersListView.render().el);
      this.$('.org-rename').tooltip({
        container: this.el
      });
      this.$('.download-key').tooltip();
      return this;
    },
    onSelect: function(view) {
      this.trigger('select', view);
    },
    onRename: function() {
      var modal = new ModalRenameOrgView({
        model: this.model
      });
    },
    onDelete: function() {
      var modal = new ModalDeleteOrgView({
        model: this.model
      });
    },
    onDownloadKey: function() {
    }
  });

  return OrgsListItemView;
});
