define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var ServerBandwidthModel = Backbone.Model.extend({
    defaults: {
      '1m': null,
      '5m': null,
      '30m': null,
      '2h': null,
      '1d': null
    },
    url: function() {
      return '/server/' + this.get('id') + '/bandwidth';
    },
    getGraphData: function(period, type) {
      var i;
      var points = [];
      var data = this.get(period);
      if (!data) {
        return null;
      }
      data = data[type];
      var max = 0;
      for (i = 0; i < data.length; i++) {
        max = Math.max(data[i][1], max);
        points.push({x: data[i][0], y: data[i][1]});
      }
      return {
        'max': max,
        'points': points
      };
    }
  });

  return ServerBandwidthModel;
});
