define([
  'jquery',
  'underscore',
  'backbone',
  'views/modalRenameUser',
  'text!templates/usersListItem.html'
], function($, _, Backbone, ModalRenameUserView, usersListItemTemplate) {
  'use strict';
  var UsersListItemView = Backbone.View.extend({
    className: 'user',
    template: _.template(usersListItemTemplate),
    events: {
      'click .selector': 'onSelect',
      'click .user-name': 'onRename'
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      this.$('[data-toggle="tooltip"]').tooltip();
      return this;
    },
    update: function() {
      this.$('.user-name').text(this.model.get('name'));
      if (this.model.get('status')) {
        if (!this.$('.status-icon').hasClass('online')) {
          this.$('.status-icon').removeClass('offline');
          this.$('.status-icon').addClass('online');
          this.$('.status-text').text('Online');
        }
      }
      else {
        if (!this.$('.status-icon').hasClass('offline')) {
          this.$('.status-icon').removeClass('online');
          this.$('.status-icon').addClass('offline');
          this.$('.status-text').text('Offline');
        }
      }
    },
    getSelect: function() {
      return this.$('.selector').hasClass('selected');
    },
    setSelect: function(state) {
      if (state) {
        this.$('.selector').addClass('selected');
        this.$('.selector-inner').show();
      }
      else {
        this.$('.selector').removeClass('selected');
        this.$('.selector-inner').hide();
      }
      this.trigger('select', this);
    },
    onSelect: function() {
      this.setSelect(!this.getSelect());
    },
    onRename: function() {
      var modal = new ModalRenameUserView({
        model: this.model.clone()
      });
      this.addView(modal);
    }
  });

  return UsersListItemView;
});
