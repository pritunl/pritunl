define([
  'jquery',
  'underscore',
  'backbone',
  'models/event'
], function($, _, Backbone, EventModel) {
  'use strict';
  var EventCollection = Backbone.Collection.extend({
    model: EventModel,
    url: function() {
      var url = '/event';
      if (this.cursor) {
        url += '/' + this.cursor;
      }
      return url;
    },
    callFetch: function(uuid) {
      if (!window.authenticated) {
        setTimeout(function() {
          this.callFetch(uuid);
        }.bind(this), 250);
        return;
      }
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
            this.cursor = model.get('id');

            if (this.cursor === 'demo') {
              this.disable();
              return;
            }

            if (!window.authenticated) {
              continue;
            }

            if (model.get('type') === 'reload') {
              location.reload();
              return;
            }

            this.trigger(model.get('type'));
            if (model.get('resource_id')) {
              this.trigger(model.get('type') + ':' +
                model.get('resource_id'));
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
      if (this.disabled) {
        return;
      }
      this.currentLoop = new Date().getTime();
      this.callFetch(this.currentLoop);
    },
    stop: function() {
      this.currentLoop = null;
    },
    disable: function() {
      this.currentLoop = null;
      this.disabled = true;
    }
  });

  return EventCollection;
});
