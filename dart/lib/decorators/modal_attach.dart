library modal_attach;

import 'package:angular/angular.dart' show Decorator, NgAttr;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;

@Decorator(
  selector: '[modal-attach]'
)
class ModalAttachDec {
  var element;
  var state;

  @NgAttr('modal-attach')
  var modalAttach;

  get modal {
    var modal;
    var selector = this.modalAttach;

    if (selector != '' && selector != null) {
      modal = this.element.parent.querySelector(selector);
    }
    else {
      modal = this.element.previousElementSibling;
    }

    return ng.ngDirectives(modal)[0];
  }

  show() {
    this.modal.open();
  }

  hide() {
    this.modal.close();
  }

  ModalAttachDec(dom.Element this.element) {
    this.element.onClick.listen((_) {
      this.show();
    });
  }
}
