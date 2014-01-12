/*jshint -W098:true */
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
        console.log('time: ' +
          response.getResponseHeader('X-Execution-Time') + 'ms');
        _complete(response);
      };
      return _ajax.call(Backbone.$, options);
    };
  };

  return initialize;
});
