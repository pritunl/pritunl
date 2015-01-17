library modal_attach;

import 'package:pritunl/bases/modal.dart' as modal_base;
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

  modal_base.ModalBase get modalBase {
    var modalElem;
    var selector = this.modalAttach;

    if (selector != '' && selector != null) {
      modalElem = this.element.parent.querySelector(selector);
    }
    else {
      modalElem = this.element.previousElementSibling;
    }

    return utils.getDirective(modalElem);
  }

  ModalAttachDec(this.element) {
    this.element.onClick.listen((_) {
      this.modalBase.show();
    });
  }
}
