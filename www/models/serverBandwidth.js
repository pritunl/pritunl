define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var ServerBandwidthModel = Backbone.Model.extend({
    defaults: {
      'received': null,
      'sent': null
    },
    url: function() {
      return '/server/' + this.get('id') + '/bandwidth/' + this.getPeriod();
    },
    getPeriod: function() {
      return this.period;
    },
    setPeriod: function(period) {
      this.period = period;
    },
    getGraphData: function(type) {
      var i;
      var points = [];
      var data = this.get(type);
      if (!data) {
        return null;
      }
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
