/* jshint -W098:true */
define([
  'jquery',
  'underscore',
  'backbone',
  'demo/ajax'
], function($, _, Backbone, demoAjax) {
  'use strict';
  var initialize = function() {
    window.demo = true;
    Backbone.ajax = demoAjax;
  };

  return initialize;
});
