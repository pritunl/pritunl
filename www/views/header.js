define([
  'jquery',
  'underscore',
  'backbone',
  'views/alert',
  'views/modalChangePassword',
  'text!templates/header.html'
], function($, _, Backbone, AlertView, ModalChangePasswordView,
    headerTemplate) {
  'use strict';
  var HeaderView = Backbone.View.extend({
    tagName: 'header',
    template: _.template(headerTemplate),
    events: {
      'click .change-password a': 'changePassword'
    },
    render: function() {
      this.$el.html(this.template());
      return this;
    },
    changePassword: function() {
      var modal = new ModalChangePasswordView();
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'warning',
          message: 'Successfully changed password.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
        this.addView(alertView);
      }.bind(this));
      this.addView(modal);
    }
  });

  return HeaderView;
});
