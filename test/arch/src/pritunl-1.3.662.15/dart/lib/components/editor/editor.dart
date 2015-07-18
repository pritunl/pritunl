library editor_comp;

import 'package:angular/angular.dart' show Component, NgAttr, NgOneWay;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;
import 'dart:js' as js;
import 'dart:async' as async;

@Component(
  selector: 'x-editor',
  template: '<div class="editor"></div>',
  cssUrl: 'packages/pritunl/components/editor/editor.css'
)
class EditorComp implements ng.ShadowRootAware {
  js.JsObject _editor;
  String _lastLine;
  dom.ShadowRoot root;

  @NgAttr('width')
  String width;

  @NgAttr('height')
  String height;

  var _content;
  @NgOneWay('content')
  void set content(List<String> value) {
    this._content = value;

    if (this._editor != null) {
      this._setContent(value);
    }
  }
  List<String> get content {
    return this._content;
  }

  void scrollBottom([int count]) {
    if (count == null) {
      count = 0;
    }
    else if (count >= 10) {
      return;
    }
    count += 1;

    var scroll = this.root.querySelector('.ace_scrollbar').scrollHeight;
    this.root.querySelector('.ace_scrollbar').scrollTop = scroll;

    new async.Timer(const Duration(milliseconds: 25), () {
      this.scrollBottom(count);
    });
  }

  void _setContent(List<String> content) {
    var foundLastLine;
    var doc = this._editor.callMethod('getSession').callMethod(
      'getDocument');

    if (content == null) {
      doc.callMethod('setValue', ['']);
      return;
    }

    if (this._lastLine != null) {
      var lines = [];
      for (var line in content.reversed) {
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
      var lines = '';

      for (var line in content) {
        lines += '$line\n';
      }

      doc.callMethod('setValue', [lines]);
      this.scrollBottom();
    }

    if (content.length > 0) {
      this._lastLine = content.last;
    }
  }

  onShadowRoot(dom.ShadowRoot root) {
    this.root = root;

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
