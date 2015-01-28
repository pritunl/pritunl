library modal_attach_dec;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content;
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

  ModalAttachDec(this.element) {
    this.element.onClick.listen((_) {
      this.show();
    });
  }

  dom.Element get modalBaseElem {
    var modalElem;
    var selector = this.modalAttach;

    if (selector != '' && selector != null) {
      var element = this.element.parent;

      while (true) {
        modalElem = element.querySelector(selector);

        if (modalElem != null) {
          break;
        }

        element = element.parent;
      }
    }
    else {
      modalElem = this.element.previousElementSibling;
    }

    return modalElem;
  }

  modal_content.ModalContent get modalBase {
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
    modalBase.show();
    this.modalDec.show(modalBase.submit, modalBase.cancel);
  }
}
