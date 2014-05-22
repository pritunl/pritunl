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
    className: 'users-list',
    template: _.template(orgsListItemTemplate),
    events: {
      'click .org-title': 'onRename',
      'click .org-del': 'onDelete',
      'click .toggle-hidden': 'onToggleHidden',
      'keyup .org-search': 'onSearch',
      'paste .org-search': 'onSearch',
      'input .org-search': 'onSearch',
      'propertychange .org-search': 'onSearch'
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
      this.$('.user-count').text(this.model.get('user_count') + ' users');
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      this.$el.append(this.usersListView.render().el);
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
    onToggleHidden: function(evt) {
      if (!evt.ctrlKey && !evt.shiftKey) {
        return;
      }
      if (this.usersListView.showHidden) {
        this.usersListView.showHidden = false;
        this.$('.toggle-hidden').removeClass('label-primary');
        this.$('.toggle-hidden').addClass('label-success');
        this.$('.toggle-hidden').tooltip('destroy');
        this.$el.removeClass('show-hidden');
      }
      else {
        this.usersListView.showHidden = true;
        this.$('.toggle-hidden').removeClass('label-success');
        this.$('.toggle-hidden').addClass('label-primary');
        this.$('.toggle-hidden').tooltip({
          title: 'Showing server users'
        });
        this.$('.toggle-hidden').tooltip('show');
        this.$el.addClass('show-hidden');
      }
      this.usersListView.update();
    },
    onSearch: function(evt) {
      var term = $(evt.target).val();
      this.curSearchTerm = term;

      setTimeout(function() {
        if (term !== this.curSearchTerm) {
          return;
        }
        if (this.curSearchTerm === '') {
          term = null;
        }
        this.usersListView.search(term);
      }.bind(this), 50);
    }
  });

  return OrgsListItemView;
});
