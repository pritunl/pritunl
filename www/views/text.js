define([
  'jquery',
  'underscore',
  'backbone',
  'ace',
  'aceModeSh',
  'aceModeText',
  'aceThemeAmbiance',
  'aceThemeChrome',
  'aceThemeGithub',
  'aceThemeMonokai',
  'aceThemeTwilight'
], function($, _, Backbone, Ace, AceModeSh, AceModeText, AceThemeAmbiance,
    AceThemeChrome, AceThemeGithub, AceThemeMonokai, AceThemeTwilight) {
  'use strict';
  var TextView = Backbone.View.extend({
    className: 'text-viewer',
    render: function() {
      this.editor = Ace.edit(this.el);
      this.editor.setTheme('ace/theme/ambiance');
      this.editor.setReadOnly(true);
      this.editor.setPrintMarginColumn(100);
      this.editor.getSession().setMode('ace/mode/sh');
      this.update();
      return this;
    },
    update: function() {
    },
    setData: function(data) {
      this.editor.setValue(data);
      this.editor.navigateFileEnd();
    },
  });

  return TextView;
});
