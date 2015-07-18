define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var ServerLinkModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'server': null,
      'name': null,
      'use_local_address': null
    },
    url: function() {
      var url = '/server/' + this.get('server') + '/link';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return ServerLinkModel;
});
