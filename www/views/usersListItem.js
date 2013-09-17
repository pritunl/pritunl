define([
  'jquery',
  'underscore',
  'backbone',
  'views/modalRenameUser',
  'text!templates/usersListItem.html'
], function($, _, Backbone, ModalRenameUserView, usersListItemTemplate) {
  'use strict';
  var UsersListItemView = Backbone.View.extend({
    template: _.template(usersListItemTemplate),
    events: {
      'click .select': 'onSelect',
      'click .user-name': 'onRename'
    },
    initialize: function() {
      this.children = [];
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      this.$('.user-name').tooltip();
      return this;
    },
    deinitialize: function() {
      if (this.renameUserView) {
        this.children.push(renameUserView);
      }
    },
    getSelect: function() {
      return this.$el.hasClass('selected');
    },
    setSelect: function(state) {
      if (state) {
        this.$el.addClass('selected');
        this.$('.select-inner').show();
      }
      else {
        this.$el.removeClass('selected');
        this.$('.select-inner').hide();
      }
      this.trigger('select', this);
    },
    onSelect: function() {
      this.setSelect(!this.getSelect());
    },
    onRename: function() {
      if (this.renameUserView) {
        this.renameUserView.destroy();
        this.renameUserView = null;
      }
      this.renameUserView = new ModalRenameUserView({
        model: this.model
      });
    }
  });

  return UsersListItemView;
});
