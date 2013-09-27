define([
  'jquery',
  'underscore',
  'backbone',
  'models/serverOutput',
  'views/text'
], function($, _, Backbone, ServerOutputModel, TextView) {
  'use strict';
  var ServerOutputView = TextView.extend({
    initialize: function(options) {
      this.model = new ServerOutputModel({
        id: options.server
      });
    },
    update: function() {
      this.model.fetch({
        success: function() {
          this.setData(this.model.get('output'));
        }.bind(this)
      });
    }
  });

  return ServerOutputView;
});
