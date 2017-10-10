define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'views/logs'
], function($, _, Backbone, ModalView, AlertView, LogsView) {
  'use strict';
  var ModalLogsView = ModalView.extend({
    className: 'logs-modal',
    title: 'System Logs',
    okText: 'Close',
    cancelText: null,
    initialize: function() {
      this.logsView = new LogsView();
      this.addView(this.logsView);
      ModalLogsView.__super__.initialize.call(this);
    },
    postRender: function() {
      this.$('.modal-body').append(
        this.logsView.render().el);
    }
  });

  return ModalLogsView;
});
