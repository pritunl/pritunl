library modal_attach;

import 'package:pritunl/components/modal/modal.dart' as mdl;

import 'package:angular/angular.dart' show Decorator, NgAttr;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;

@Decorator(
  selector: '[modal-attach]'
)
class ModalAttachDec {
  dom.Element element;
  bool state;

  @NgAttr('modal-attach')
  String modalAttach;

  mdl.ModalComp get modal {
    var modal;
    var selector = this.modalAttach;

    if (selector != '' && selector != null) {
      modal = this.element.parent.querySelector(selector);
      if (modal.nodeName != 'MODAL') {
        modal = modal.shadowRoot.querySelector('modal');
      }
    }
    else {
      modal = this.element.previousElementSibling;
    }

    return ng.ngDirectives(modal)[0];
  }

  void show() {
    this.modal.open();
  }

  void hide() {
    this.modal.close();
  }

  ModalAttachDec(this.element) {
    this.element.onClick.listen((_) {
      this.show();
    });
  }
}
