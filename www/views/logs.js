define([
  'jquery',
  'underscore',
  'backbone',
  'models/logs',
  'views/text',
  'views/alert'
], function($, _, Backbone, LogsModel, TextView, AlertView) {
  'use strict';
  var LogsView = TextView.extend({
    errorMsg: 'Failed to load system logs, server error occurred.',
    initialize: function() {
      this.scroll = true;
      this.model = new LogsModel();
      this.listenTo(window.events, 'system_log_updated', this.update);
    },
    update: function() {
      this.model.fetch({
        error: function() {
          var alertView = new AlertView({
            type: 'danger',
            message: this.errorMsg,
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
          this.setData('');
        }.bind(this),
        success: function() {
          this.setData(this.model.get('output'));
          if (this.scroll) {
            this.scroll = false;
            setTimeout(function() {
              this.scrollBottom();
              setTimeout(function() {
                this.scrollBottom();
              }.bind(this), 275);
            }.bind(this), 275);
          }
        }.bind(this)
      });
    }
  });

  return LogsView;
});
