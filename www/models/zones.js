define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var ZonesModel = Backbone.Model.extend({
    defaults: {
      'us-east-1': [],
      'us-east-2': [],
      'us-west-1': [],
      'us-west-2': [],
      'us-gov-west-1': [],
      'eu-west-1': [],
      'eu-central-1': [],
      'ap-northeast-1': [],
      'ap-northeast-2': [],
      'ap-southeast-1': [],
      'ap-southeast-2': [],
      'ap-south-1': [],
      'sa-east-1': []
    },
    url: '/settings/zones'
  });

  return ZonesModel;
});
