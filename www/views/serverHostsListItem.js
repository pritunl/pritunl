define([
  'jquery',
  'underscore',
  'backbone',
  'views/alert',
  'views/modalDetachHost',
  'text!templates/serverHostsListItem.html'
], function($, _, Backbone, AlertView, ModalDetachHostView,
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
      if (this.$('.host-address')) {
        this.$('.host-address').text('(' + this.model.get('address') + ')');
      }
      else {
        this.$('.host-address').text('');
      }
      if (this.model.get('status') === 'online') {
        this.$('.host-offline').hide();
        this.$('.host-online').show();
      }
      else if (this.model.get('status') === 'offline') {
        this.$('.host-online').hide();
        this.$('.host-offline').show();
      }
      else {
        this.$('.host-online').hide();
        this.$('.host-offline').hide();
      }
    },
    onDetach: function(evt) {
      var model = this.model.clone();

      if (evt.shiftKey && evt.ctrlKey && evt.altKey) {
        model.destroy();
        return;
      }

      var modal = new ModalDetachHostView({
        model: model
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
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
