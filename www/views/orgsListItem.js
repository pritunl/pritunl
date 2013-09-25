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
      'click .download-key': 'onDownloadKey',
      'click .toggle-hidden': 'onToggleHidden'
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
        // TODO View is already destroyed
        return;
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
    },
    onToggleHidden: function(evt) {
      if (!evt.shiftKey) {
        return;
      }
      if (this.usersListView.showHidden) {
        this.usersListView.showHidden = false;
        this.$('.toggle-hidden').removeClass('label-primary');
        this.$('.toggle-hidden').addClass('label-success');
        this.$('.toggle-hidden').tooltip('destroy');
      }
      else {
        this.usersListView.showHidden = true;
        this.$('.toggle-hidden').removeClass('label-success');
        this.$('.toggle-hidden').addClass('label-primary');
        this.$('.toggle-hidden').tooltip({
          title: 'Showing hidden users'
        });
        this.$('.toggle-hidden').tooltip('show');
      }
      this.usersListView.update();
    }
  });

  return OrgsListItemView;
});
