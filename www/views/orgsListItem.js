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
      'click .org-title': 'onRename',
      'click .org-del': 'onDelete',
      'click .download-key': 'onDownloadKey'
    },
    initialize: function() {
      this.usersListView = new UsersListView({
        org: this.model.get('id')
      });
      this.addView(this.usersListView);
      this.listenTo(this.usersListView, 'select', this.onSelect);
    },
    update: function() {
      this.$('.org-title').text(this.model.get('name'));
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      this.$('.users-list').append(this.usersListView.render().el);
      this.$('.org-title').tooltip({
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
        model: this.model.clone()
      });
      this.addView(modal);
    },
    onDelete: function() {
      var modal = new ModalDeleteOrgView({
        model: this.model
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'warning',
          message: 'Successfully deleted organization.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    },
    onDownloadKey: function() {
    }
  });

  return OrgsListItemView;
});
