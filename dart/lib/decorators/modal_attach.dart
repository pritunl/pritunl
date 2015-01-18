library modal_attach;

import 'package:pritunl/components/modal_base/modal_base.dart' as modal_base;
import 'package:pritunl/decorators/modal.dart' as modal_dec;
import 'package:pritunl/utils/utils.dart' as utils;

import 'package:angular/angular.dart' show Decorator, NgAttr;
import 'dart:html' as dom;

@Decorator(
  selector: '[modal-attach]'
)
class ModalAttachDec {
  dom.Element element;

  @NgAttr('modal-attach')
  String modalAttach;

  dom.Element get modalBaseElem {
    var modalElem;
    var selector = this.modalAttach;

    if (selector != '' && selector != null) {
      modalElem = this.element.parent.querySelector(selector);
    }
    else {
      modalElem = this.element.previousElementSibling;
    }

    return modalElem;
  }

  modal_base.ModalBase get modalBase {
    return utils.getDirective(this.modalBaseElem);
  }

  modal_dec.ModalDec get modalDec {
    for (var node in this.modalBaseElem.shadowRoot.nodes) {
      var directive = utils.getDirective(node, modal_dec.ModalDec);
      if (directive != null) {
        return directive;
      }
    }
    return null;
  }

  void show() {
    var modalBase = this.modalBase;
    this.modalDec.show(modalBase.submit, modalBase.cancel);
  }

  ModalAttachDec(this.element) {
    this.element.onClick.listen((_) {
      this.show();
    });
  }
}
