library editor_comp;

import 'package:angular/angular.dart' show Component, NgAttr, NgOneWay;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;
import 'dart:js' as js;

@Component(
  selector: 'editor',
  templateUrl: 'packages/pritunl/components/editor/editor.html',
  cssUrl: 'packages/pritunl/components/editor/editor.css'
)
class EditorComp implements ng.ShadowRootAware {
  js.JsObject _editor;

  @NgAttr('width')
  String width;

  @NgAttr('height')
  String height;

  String _content;
  @NgOneWay('content')
  void set content(String value) {
    this._content = value;

    if (this._editor != null) {
      this._editor.callMethod('getSession').callMethod(
        'getDocument').callMethod('setValue', [value]);
    }
  }
  String get content {
    return this._content;
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

    editor.callMethod('getSession').callMethod(
      'getDocument').callMethod('setValue', [this.content]);

    var styles = dom.document.head.querySelectorAll('#ace_editor, #ace-tm');

    for (var style in styles) {
      root.children.add(style.clone(true));
    }

    this._editor = editor;
  }
}
