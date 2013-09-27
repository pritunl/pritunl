define([
  'jquery',
  'underscore',
  'backbone',
  'models/serverOutput',
  'views/text',
  'views/alert'
], function($, _, Backbone, ServerOutputModel, TextView, AlertView) {
  'use strict';
  var ServerOutputView = TextView.extend({
    initialize: function(options) {
      this.model = new ServerOutputModel({
        id: options.server
      });
    },
    update: function() {
      this.model.fetch({
        error: function() {
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to load server output, server error occurred.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
          this.setData('');
        }.bind(this),
        success: function() {
          this.setData(this.model.get('output'));
        }.bind(this)
      });
    }
  });

  return ServerOutputView;
});
