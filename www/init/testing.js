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
      var _complete = options.complete;
      options.complete = function(response) {
        console.log('%c' +
          response.getResponseHeader('X-Execution-Time') + 'ms ' +
          this.url, 'color: #0066ff');
        _complete(response);
      };
      return _ajax.call(Backbone.$, options);
    };
  };

  return initialize;
});
