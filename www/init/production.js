/* jshint -W098:true, -W117:true */
define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone) {
  'use strict';
  var initialize = function() {
    var _ajax = Backbone.ajax;
    Backbone.ajax = function(options) {
      var _headers = options.headers;
      var headers = {
        'Csrf-Token': window.csrfToken
      };

      if (_headers) {
        options.headers = _.extend(headers, _headers);
      } else {
        options.headers = headers;
      }

      var _complete = options.complete;
      options.complete = function(response) {
        if (this.url.substring(0, 6) !== '/event') {
          var execTime = response.getResponseHeader('Execution-Time');
          if (!execTime) {
            return;
          }
          var queryTime = response.getResponseHeader('Query-Time');
          if (!queryTime) {
            return;
          }
          var queryCount = response.getResponseHeader('Query-Count');
          if (!queryCount) {
            return;
          }
          var writeCount = response.getResponseHeader('Write-Count');
          if (!queryCount) {
            return;
          }
          var color;
          if (execTime > 200) {
            color = '#ff0000';
          }
          else if (execTime > 100) {
            color = '#ff6b0d';
          }
          else {
            color = '#0066ff';
          }
          console.log('%c' + execTime + 'ms ' + queryTime + 'ms ' +
            queryCount + 'dbq ' + writeCount + 'dbw ' + this.url,
            'color: ' + color);
        }
        if (_complete) {
          _complete(response);
        }
      };
      return _ajax.call(Backbone.$, options);
    };
  };

  return initialize;
});
