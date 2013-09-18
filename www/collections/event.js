define([
  'jquery',
  'underscore',
  'backbone',
  'models/event'
], function($, _, Backbone, EventModel) {
  'use strict';
  var EventCollection = Backbone.Collection.extend({
    model: EventModel,
    initialize: function() {
      this.processedEvents = [];
    },
    url: function() {
      var url = '/event';
      if (this.lastEventTime) {
        url += '/' + this.lastEventTime;
      }
      return url;
    },
    callFetch: function(uuid) {
      this.fetch({
        reset: true,
        success: function(collection) {
          if (uuid !== this.currentLoop) {
            return;
          }
          var i;
          var model;

          for (i = 0; i < collection.models.length; i++) {
            model = collection.models[i];

            if (this.processedEvents.indexOf(model.get('id')) !== -1) {
              continue;
            }
            this.processedEvents.push(model.get('id'));

            if (!this.lastEventTime ||
                model.get('time') > this.lastEventTime) {
              this.lastEventTime = model.get('time');
            }

            // Ignore callback for time events
            if (model.get('type') !== 'time') {
              this.trigger(model.get('type'));
            }
          }

          this.callFetch(uuid);
        }.bind(this),
        error: function() {
          if (uuid !== this.currentLoop) {
            return;
          }
          setTimeout(function() {
            this.callFetch(uuid);
          }.bind(this), 1000);
        }.bind(this)
      });
    },
    start: function() {
      this.currentLoop = new Date().getTime();
      this.callFetch(this.currentLoop);
    },
    stop: function() {
      this.currentLoop = null;
    }
  });

  return EventCollection;
});
