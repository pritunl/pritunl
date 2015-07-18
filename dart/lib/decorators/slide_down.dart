library slide_down_dec;

import 'package:angular/angular.dart' show Decorator, NgOneWay;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;

@Decorator(
  selector: '[slide-down]',
  children: 'transclude'
)
class SlideDownDec {
  final ng.ViewFactory _viewFactory;
  final ng.ViewPort _viewPort;
  final ng.Scope _scope;
  ng.View _view;
  dom.Element element;

  @NgOneWay('.')
  void set slide(var slideTime) {
    print('set-slide');
    this._ensureViewExists();
    print(this.element.innerHtml);
  }

  SlideDownDec(this._viewFactory, this._viewPort, this._scope);

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
