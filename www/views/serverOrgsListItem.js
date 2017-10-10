define([
  'jquery',
  'underscore',
  'backbone',
  'views/alert',
  'views/modalDetachOrg',
  'text!templates/serverOrgsListItem.html'
], function($, _, Backbone, AlertView, ModalDetachOrg,
    serverOrgsListItemTemplate) {
  'use strict';
  var ServerOrgsListItemView = Backbone.View.extend({
    className: 'org',
    template: _.template(serverOrgsListItemTemplate),
    events: {
      'click .server-detach-org': 'onDetachOrg'
    },
    initialize: function(options) {
      this.server = options.server;
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    },
    update: function() {
      this.$('.org-name').text(this.model.get('name'));
    },
    onDetachOrg: function(evt) {
      if (this.server.get('status') === 'online') {
        var alertView = new AlertView({
          type: 'danger',
          message: 'Server must be offline to detach an organization.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        return;
      }

      var model = this.model.clone();

      if (evt.shiftKey && evt.ctrlKey && evt.altKey) {
        model.destroy();
        return;
      }

      var modal = new ModalDetachOrg({
        model: model
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
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
