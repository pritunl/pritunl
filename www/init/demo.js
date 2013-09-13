define([
  'jquery',
  'underscore',
  'backbone',
  'googleAnalytics'
], function($, _, Backbone, GoogleAnalytics) {
  'use strict';
  var initialize = function() {
    GoogleAnalytics.push(['_setAccount', '']);
    //GoogleAnalytics.push(['_setDomainName', 'demo.pritunl.com']);
  };

  return initialize;
});
