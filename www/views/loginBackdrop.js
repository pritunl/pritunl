define([
  'jquery',
  'underscore',
  'backbone'
], function($, _, Backbone, loginTemplate) {
  'use strict';
  var LoginBackdropView = Backbone.View.extend({
    className: 'login-backdrop'
  });

  return LoginBackdropView;
});
