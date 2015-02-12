library editor_comp;

import 'package:angular/angular.dart' show Component, NgAttr, NgOneWay;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;
import 'dart:js' as js;

@Component(
  selector: 'editor',
  template: '<div class="editor"></div>',
  cssUrl: 'packages/pritunl/components/editor/editor.css'
)
class EditorComp implements ng.ShadowRootAware {
  js.JsObject _editor;
  String _lastLine;

  @NgAttr('width')
  String width;

  @NgAttr('height')
  String height;

  var _content;
  @NgOneWay('content')
  void set content(String value) {
    this._content = value;

    if (this._editor != null) {
      this._setContent(value);
    }
  }
  String get content {
    return this._content;
  }

  void _setContent(String content) {
    var foundLastLine;
    var contentSplit = content.split('\n');
    var doc = this._editor.callMethod('getSession').callMethod(
      'getDocument');

    if (this._lastLine != null) {
      var lines = [];
      for (var line in contentSplit.reversed) {
        if (line == this._lastLine) {
          foundLastLine = true;
          break;
        }
        lines.add(line);
      }

      if (foundLastLine != true) {
        this._lastLine = null;
      }
      else if (lines.length > 0) {
        var docLen = doc.callMethod('getLength');
        doc.callMethod('insertLines', [docLen - 1,
          new js.JsArray.from(lines.reversed)]);
      }
    }

    if (this._lastLine == null) {
      doc.callMethod('setValue', [content]);
    }

    if (contentSplit.length > 0) {
      this._lastLine = contentSplit[contentSplit.length - 1];
    }
  }

  onShadowRoot(dom.ShadowRoot root) {
    var editorDiv = root.querySelector('.editor');

    editorDiv.style.width = this.width;
    editorDiv.style.height = this.height;

    var editor = js.context['ace'].callMethod('edit', [editorDiv]);
    editor.callMethod('setTheme', ['ace/theme/pritunl']);
    editor.callMethod('setFontSize', [10]);
    editor.callMethod('setReadOnly', [true]);
    editor.callMethod('setShowPrintMargin', [false]);
    editor.callMethod('setHighlightActiveLine', [false]);
    editor.callMethod('setHighlightGutterLine', [false]);
    editor.callMethod('setShowFoldWidgets', [false]);
    editor.callMethod('getSession').callMethod('setMode', ['ace/mode/log']);

    var styles = dom.document.head.querySelectorAll('#ace_editor, #ace-tm');

    for (var style in styles) {
      root.children.add(style.clone(true));
    }

    this._editor = editor;

    this._setContent(this.content);
  }
}
