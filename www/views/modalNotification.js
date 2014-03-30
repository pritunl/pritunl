define([
  'jquery',
  'underscore',
  'backbone',
  'models/org',
  'views/modal',
  'text!templates/modalNotification.html'
], function($, _, Backbone, OrgModel, ModalView, modalNotificationTemplate) {
  'use strict';
  var ModalNotificationView = ModalView.extend({
    className: 'notification-modal',
    template: _.template(modalNotificationTemplate),
    title: 'Update Notification',
    okText: 'Close',
    cancelText: null,
    body: function() {
      return this.template(this.model.toJSON());
    }
  });

  return ModalNotificationView;
});
