define([
  'jquery',
  'underscore',
  'backbone',
  'rickshaw',
  'models/hostUsage',
  'views/alert',
  'text!templates/hostUsage.html'
], function($, _, Backbone, Rickshaw, HostUsageModel, AlertView,
    hostUsageTemplate) {
  'use strict';
  var UsageHover = Rickshaw.Class.create(Rickshaw.Graph.HoverDetail, {
    initialize: function(args) {
      _.extend(args, {
        xFormatter: function(x) {
          // Pad length for rickshaw width calc
          return window.formatTime(x) + '#####';
        },
        yFormatter: function(y) {
          return (y * 100).toFixed(1) + '%';
        },
        onRender: function(args) {
          $(this.graph.element).find('.detail .x_label').html(
            $('<span>').text(args.formattedXValue.replace('#####', '') +
            ' (' + args.detail[0].series.period  + ')').html() + '<br>' +
            $('<span>').text(args.detail[0].name + ': ' +
              args.detail[0].formattedYValue).html());
        }
      });
      Rickshaw.Graph.HoverDetail.prototype.initialize.call(this, args);
    }
  });

  var HostUsageView = Backbone.View.extend({
    template: _.template(hostUsageTemplate),
    initialize: function(options) {
      this.model = new HostUsageModel({
        id: options.host
      });
      this.model.setPeriod('1m');
      this.state = false;
      this.interval = setInterval((this.update).bind(this), 15000);
      this.update();

      this.bindId = window.uuid();
      this.width = this.$el.width();
      $(window).bind('resize.' + this.bindId, (this.onResize).bind(this));
    },
    deinitialize: function() {
      clearInterval(this.interval);
      $(window).unbind('resize.' + this.bindId);
    },
    onResize: function() {
      var width = this.$el.width();
      if (width !== this.width) {
        this.width = width;
        this.$el.empty();
        this.render();
      }
    },
    render: function() {
      this.$el.html(this.template());
      this.updateGraph();
      return this;
    },
    update: function() {
      this.model.fetch({
        error: function() {
          var alertView = new AlertView({
            type: 'danger',
            message: 'Failed to load server bandwidth, server error occurred.',
            dismissable: true
          });
          $('.alerts-container').append(alertView.render().el);
          this.addView(alertView);
        }.bind(this),
        success: function() {
          this.$el.empty();
          this.render();
        }.bind(this)
      });
    },
    setType: function(graphType) {
      if (this.getType() === graphType) {
        return;
      }
      this.graphType = graphType;
      if (graphType === 'cpu') {
        this.$('.host-graph-mem').hide();
        this.$('.host-graph-cpu').show();
      }
      else {
        this.$('.host-graph-cpu').hide();
        this.$('.host-graph-mem').show();
      }
    },
    getType: function() {
      return this.graphType || 'cpu';
    },
    setPeriod: function(period) {
      if (this.getPeriod() === period) {
        return;
      }
      this.model.setPeriod(period);
      this.update();
    },
    getPeriod: function() {
      return this.model.getPeriod();
    },
    updateGraph: function() {
      var cpuUsage = this.model.getGraphData('cpu');
      var memUsage = this.model.getGraphData('mem');

      if (!cpuUsage || !memUsage) {
        return;
      }

      if (this.getPeriod() === '1m') {
        cpuUsage.pop();
        memUsage.pop();
      }

      var width = this.$el.width();
      var height = this.$el.height() - 2;

      var graphCpu = new Rickshaw.Graph({
        element: this.$('.host-graph-cpu')[0],
        width: width,
        height: height,
        renderer: 'area',
        stroke: true,
        max: 1,
        series: [{
          period: this.getPeriod(),
          name: 'CPU Usage',
          color: 'rgba(44, 127, 184, 0.05)',
          stroke: '#2c7fb8',
          data: cpuUsage
        }]
      });
      graphCpu.render();
      if (this.getType() === 'cpu') {
        this.$('.host-graph-cpu').show();
      }
      else {
        this.$('.host-graph-cpu').hide();
      }
      var xAxisRecv = new Rickshaw.Graph.Axis.Time({
        graph: graphCpu
      });
      xAxisRecv.render();
      new UsageHover({
        graph: graphCpu
      });

      var graphMem = new Rickshaw.Graph({
        element: this.$('.host-graph-mem')[0],
        width: width,
        height: height,
        renderer: 'area',
        stroke: true,
        max: 1,
        series: [{
          period: this.getPeriod(),
          name: 'Memory Usage',
          color: 'rgba(44, 127, 184, 0.05)',
          stroke: '#2c7fb8',
          data: memUsage
        }]
      });
      graphMem.render();
      if (this.getType() === 'mem') {
        this.$('.host-graph-mem').show();
      }
      else {
        this.$('.host-graph-mem').hide();
      }
      var xAxisSent = new Rickshaw.Graph.Axis.Time({
        graph: graphMem
      });
      xAxisSent.render();
      new UsageHover({
        graph: graphMem
      });
    }
  });

  return HostUsageView;
});
