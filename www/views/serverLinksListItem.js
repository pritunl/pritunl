define([
  'jquery',
  'underscore',
  'backbone',
  'views/alert',
  'views/modalDetachLink',
  'text!templates/serverLinksListItem.html'
], function($, _, Backbone, AlertView, ModalDetachLink,
    serverLinksListItemTemplate) {
  'use strict';
  var ServerLinksListItemView = Backbone.View.extend({
    className: 'link',
    template: _.template(serverLinksListItemTemplate),
    events: {
      'click .server-detach-link': 'onDetach'
    },
    initialize: function(options) {
      this.server = options.server;
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    },
    update: function() {
      this.$('.link-name').text(this.model.get('name'));
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
    onDetach: function() {
      var modal = new ModalDetachLink({
        model: this.model.clone()
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'warning',
          message: 'Successfully detached link.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    }
  });

  return ServerLinksListItemView;
});
