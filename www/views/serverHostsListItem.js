define([
  'jquery',
  'underscore',
  'backbone',
  'views/alert',
  'views/modalDetachHost',
  'text!templates/serverHostsListItem.html'
], function($, _, Backbone, AlertView, ModalDetachHost,
    serverHostsListItemTemplate) {
  'use strict';
  var ServerHostsListItemView = Backbone.View.extend({
    className: 'host',
    template: _.template(serverHostsListItemTemplate),
    events: {
      'click .server-detach-host': 'onDetach'
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
    onDetach: function() {
      var modal = new ModalDetachHost({
        model: this.model.clone()
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'warning',
          message: 'Successfully detached host.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    }
  });

  return ServerHostsListItemView;
});
