define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var HostUsageModel = Backbone.Model.extend({
    defaults: {
      'cpu': null,
      'mem': null
    },
    url: function() {
      return '/host/' + this.get('id') + '/usage/' + this.getPeriod();
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
      for (i = 0; i < data.length; i++) {
        points.push({x: data[i][0], y: data[i][1]});
      }
      return points;
    }
  });

  return HostUsageModel;
});
