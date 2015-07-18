/* jshint -W098:true */
define([
  'jquery',
  'underscore',
  'backbone',
  'ace',
  'aceModeLog',
  'aceModeSh',
  'aceModeText',
  'aceThemePritunl'
], function($, _, Backbone, Ace, AceModeLog, AceModeSh, AceModeText,
    AceThemePritunl) {
  'use strict';
  var TextView = Backbone.View.extend({
    className: 'text-viewer',
    initialize: function() {
      this.lastLine = null;
    },
    render: function() {
      this.editor = Ace.edit(this.el);
      this.editor.setTheme('ace/theme/pritunl');
      this.editor.setFontSize(10);
      this.editor.setReadOnly(true);
      this.editor.setShowPrintMargin(false);
      this.editor.setHighlightActiveLine(false);
      this.editor.setHighlightGutterLine(false);
      this.editor.setShowFoldWidgets(false);
      this.editor.getSession().setMode('ace/mode/log');
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

      var $scollbar = this.$('.ace_scrollbar');
      $scollbar.scrollTop($scollbar[0].scrollHeight);

      setTimeout(function() {
        this.scrollBottom(count);
      }.bind(this), 25);
    },
    setData: function(data) {
      var i;
      var lines;
      var foundLastLine;
      var doc = this.editor.getSession().getDocument();

      if (this.lastLine) {
        lines = [];
        for (i = data.length - 1; i >= 0; i--) {
          if (data[i] === this.lastLine) {
            foundLastLine = true;
            break;
          }
          lines.push(data[i]);
        }
        if (!foundLastLine) {
          this.lastLine = null;
        }
        else if (lines) {
          doc.insertLines(doc.getLength() - 1, lines.reverse());
        }
      }

      if (!this.lastLine) {
        lines = '';
        for (i = 0; i < data.length; i++) {
          lines += data[i] + '\n';
        }
        this.editor.setValue(lines, 1);
        this.scrollBottom();
      }

      if (lines) {
        this.lastLine = data[data.length - 1];
      }
    }
  });

  return TextView;
});
