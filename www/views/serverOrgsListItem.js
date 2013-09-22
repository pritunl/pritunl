define([
  'jquery',
  'underscore',
  'backbone',
  'views/modalDetachOrg',
  'text!templates/serverOrgsListItem.html'
], function($, _, Backbone, ModalDetachOrg, serverOrgsListItemTemplate) {
  'use strict';
  var ServerOrgsListItemView = Backbone.View.extend({
    className: 'org',
    template: _.template(serverOrgsListItemTemplate),
    events: {
      'click .server-detach-org': 'onDetachOrg'
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    },
    update: function() {
      this.$('.org-name').text(this.model.get('name'));
    },
    onDetachOrg: function() {
      var modal = new ModalDetachOrg({
        model: this.model.clone()
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'warning',
          message: 'Successfully detached server organization.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    }
  });

  return ServerOrgsListItemView;
});
