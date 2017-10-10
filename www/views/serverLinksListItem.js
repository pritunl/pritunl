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
        this.$('.link-offline').hide();
        this.$('.link-online').show();
      }
      else if (this.model.get('status') === 'offline') {
        this.$('.link-online').hide();
        this.$('.link-offline').show();
      }
      else {
        this.$('.link-online').hide();
        this.$('.link-offline').hide();
      }

      if (this.model.get('use_local_address')) {
        this.$('.link-use-local').show();
      }
      else {
        this.$('.link-use-local').hide();
      }
    },
    onDetach: function(evt) {
      var model = this.model.clone();

      if (evt.shiftKey && evt.ctrlKey && evt.altKey) {
        model.destroy();
        return;
      }

      var modal = new ModalDetachLink({
        model: model
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
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
