define([
  'jquery',
  'underscore',
  'backbone',
  'views/alert',
  'views/usersList',
  'views/modalRenameOrg',
  'text!templates/orgsListItem.html'
], function($, _, Backbone, AlertView, UsersListView, ModalRenameOrgView,
    orgsListItemTemplate) {
  'use strict';
  var OrgsListItemView = Backbone.View.extend({
    template: _.template(orgsListItemTemplate),
    events: {
      'click .org-rename': 'onRenameOrg',
      'click .org-del': 'onDelOrg'
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
      return this;
    },
    onSelect: function(view) {
      this.trigger('select', view);
    },
    onRenameOrg: function() {
      var modal = new ModalRenameOrgView({
        model: this.model
      });
    },
    onDelOrg: function() {
      var alertView = new AlertView({
        type: 'warning',
        message: 'Successfully deleted organization.',
        dismissable: true
      });
      $('.alerts-container').append(alertView.render().el);
      this.$el.slideUp({
        duration: 250,
        complete: function() {
          this.remove();
        }.bind(this)
      });
    },
  });

  return OrgsListItemView;
});
