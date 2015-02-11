library editor_comp;

import 'package:angular/angular.dart' show Component, NgAttr;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;
import 'dart:js' as js;
import 'dart:async' as async;

@Component(
  selector: 'editor',
  templateUrl: 'packages/pritunl/components/editor/editor.html',
  cssUrl: 'packages/pritunl/components/editor/editor.css'
)
class EditorComp implements ng.ShadowRootAware {
  @NgAttr('width')
  String width;

  @NgAttr('height')
  String height;

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
  }
}
