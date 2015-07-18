define([
  'jquery',
  'underscore',
  'backbone',
  'models/serverOutputLink',
  'views/serverOutput'
], function($, _, Backbone, ServerOutputLinkModel, ServerOutputView) {
  'use strict';
  var ServerOutputLinkView = ServerOutputView.extend({
    errorMsg: 'Failed to load server link output, server error occurred.',
    initialize: function(options) {
      this.model = new ServerOutputLinkModel({
        id: options.server
      });
      this.state = false;
      this.listenTo(window.events, 'server_link_output_updated:' +
          options.server, this.update);
    }
  });

  return ServerOutputLinkView;
});
