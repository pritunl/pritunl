/* jshint -W098:true */
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
      this.editor.setTheme('ace/theme/chrome');
      this.editor.setFontSize(10);
      this.editor.setReadOnly(true);
      this.editor.setShowPrintMargin(false);
      this.editor.setHighlightActiveLine(false);
      this.editor.setHighlightGutterLine(false);
      this.editor.setShowFoldWidgets(false);
      this.editor.getSession().setMode('ace/mode/text');
      this.update();
      return this;
    },
    update: function() {
    },
    scrollBottom: function(count) {
      if (count === undefined) {
        count = 0;
      }
      else if (count >= 10) {
        return;
      }
      count += 1;

      this.$('.ace_scrollbar').scrollTop(
        this.$('.ace_scrollbar')[0].scrollHeight);
      setTimeout(function() {
        this.scrollBottom(count);
      }.bind(this), 25);
    },
    setData: function(data) {
      if (data && data.slice(-1) !== '\n') {
        data += '\n';
      }
      this.editor.setValue(data, 1);
      this.scrollBottom();
    },
  });

  return TextView;
});
