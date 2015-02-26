library all_aware;

import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;

class AllAware implements ng.ShadowRootAware, ng.AttachAware {
  var _root;
  var _onAll;

  void attach() {
    if (this._onAll == true || this._root == null) {
      return;
    }
    this._onAll = true;
    this.onAll(this._root);
  }

  void onShadowRoot(dom.ShadowRoot root) {
    this._root = root;
    if (this._onAll == true) {
      return;
    }
    this._onAll = true;
    this.onAll(this._root);
  }

  void onAll(dom.ShadowRoot root) {}
}
