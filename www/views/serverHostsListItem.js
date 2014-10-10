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
      this.$('.host-name').text(this.model.get('name'));
      this.$('.host-public-address').text(
        '(' + this.model.get('public_address') + ')');
      if (this.model.get('status') === 'online') {
        this.$('.host-offline').addClass('host-online');
        this.$('.host-offline').removeClass('host-offline');
      }
      else {
        this.$('.host-online').addClass('host-offline');
        this.$('.host-online').removeClass('host-online');
      }
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
