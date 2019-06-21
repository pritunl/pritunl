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
      'us-gov-east-1': [],
      'us-gov-west-1': [],
      'eu-north-1': [],
      'eu-west-1': [],
      'eu-west-2': [],
      'eu-west-3': [],
      'eu-central-1': [],
      'ca-central-1': [],
      'cn-north-1': [],
      'cn-northwest-1': [],
      'ap-northeast-1': [],
      'ap-northeast-2': [],
      'ap-southeast-1': [],
      'ap-southeast-2': [],
      'ap-east-1': [],
      'ap-south-1': [],
      'sa-east-1': []
    },
    url: '/settings/zones'
  });

  return ZonesModel;
});
