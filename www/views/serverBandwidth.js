define([
  'jquery',
  'underscore',
  'backbone',
  'rickshaw',
  'models/serverBandwidth',
  'views/alert',
  'text!templates/serverBandwidth.html'
], function($, _, Backbone, Rickshaw, ServerBandwidthModel, AlertView,
    serverBandwidthTemplate) {
  'use strict';
  var BandwidthHover = Rickshaw.Class.create(Rickshaw.Graph.HoverDetail, {
    initialize: function(args) {
      _.extend(args, {
        xFormatter: function(x) {
          return window.formatTime(x);
        },
        yFormatter: function(y) {
          return window.formatSize(y);
        },
        onRender: function(args) {
          $(this.graph.element).find('.detail .x_label').html(
            args.formattedXValue + '<br>' +
            args.detail[0].name + ': ' + args.detail[0].formattedYValue);
        }
      });
      Rickshaw.Graph.HoverDetail.prototype.initialize.call(this, args);
    },
  });

  var ServerBandwidthView = Backbone.View.extend({
    template: _.template(serverBandwidthTemplate),
    initialize: function(options) {
      this.model = new ServerBandwidthModel({
        id: options.server
      });
      this.state = false;
      this.recvPeriod = '1m';
      this.sentPeriod = '1m';
      this.listenTo(window.events, 'server_bandwidth_updated:' +
        options.server, this.update);
    },
    render: function() {
      this.$el.html(this.template());
      this.updateGraph();
      return this;
    },
    update: function() {
      if (!this.getState()) {
        return;
      }
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
    setState: function(state) {
      if (this.getState() === state) {
        return;
      }
      this.state = state;
      if (state) {
        this.$el.parent().show();
        this.update();
      }
      else {
        this.$el.parent().hide();
      }
    },
    getState: function() {
      return this.state;
    },
    updateGraph: function() {
      var dataRecv = this.model.getGraphData(this.recvPeriod, 'received');
      var dataSent = this.model.getGraphData(this.sentPeriod, 'sent');
      if (!dataRecv || !dataSent) {
        return;
      }

      var graphRecv = new Rickshaw.Graph({
        element: this.$('.server-graph-recv')[0],
        width: 585,
        height: 129,
        renderer: 'area',
        stroke: true,
        max: dataRecv.max * 1.05,
        series: [{
          name: 'Inbound',
          color: 'rgba(44, 127, 184, 0.05)',
          stroke: '#2c7fb8',
          data: dataRecv.points
        }]
      });
      graphRecv.render();
      var xAxisRecv = new Rickshaw.Graph.Axis.Time({
        graph: graphRecv
      });
      xAxisRecv.render();
      new BandwidthHover({
        graph: graphRecv
      });

      var graphSent = new Rickshaw.Graph({
        element: this.$('.server-graph-sent')[0],
        width: 585,
        height: 129,
        renderer: 'area',
        stroke: true,
        max: dataSent.max * 1.05,
        series: [{
          name: 'Outbound',
          color: 'rgba(44, 127, 184, 0.05)',
          stroke: '#2c7fb8',
          data: dataSent.points
        }],
      });
      graphSent.render();
      var xAxisSent = new Rickshaw.Graph.Axis.Time({
        graph: graphSent
      });
      xAxisSent.render();
      new BandwidthHover({
        graph: graphSent
      });
    }
  });

  return ServerBandwidthView;
});
