library conditional_dec;

import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;

abstract class Conditional {
  final ng.ViewFactory _viewFactory;
  final ng.ViewPort _viewPort;
  final ng.Scope _scope;
  ng.View _view;
  dom.Element element;

  Conditional(this._viewFactory, this._viewPort, this._scope);

  void set condition(value) {
    if (value == true) {
      this._ensureViewExists();
    } else {
      this._ensureViewDestroyed();
    }
  }

  void _ensureViewExists() {
    if (this._view == null) {
      this._view = this._viewPort.insertNew(this._viewFactory);
      this.element = this._view.nodes[0];
    }
  }

  void _ensureViewDestroyed() {
    if (this._view != null) {
      this._viewPort.remove(this._view);
      this._view = null;
      this.element = null;
    }
  }
}
