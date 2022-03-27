define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var LinkModel = Backbone.Model.extend({
    defaults: {
      'id': null,
      'name': null,
      'type': null,
      'ipv6': null,
      'host_check': null,
      'action': null,
      'status': null,
      'locations': null,
      'timeout': null,
      'preferred_ike': null,
      'preferred_esp': null,
      'force_preferred': null
    },
    url: function() {
      var url = '/link';

      if (this.get('id')) {
        url += '/' + this.get('id');
      }

      return url;
    }
  });

  return LinkModel;
});
