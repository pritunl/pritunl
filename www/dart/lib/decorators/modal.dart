library modal_dec;

import 'package:pritunl/decorators/conditional.dart' as conditional;
import 'package:pritunl/utils/utils.dart' as utils;
import 'package:pritunl/components/modal/modal.dart' as modal;

import 'package:angular/angular.dart' show Decorator;
import 'package:angular/angular.dart' as ng;
import 'dart:async' as async;

@Decorator(
  children: 'transclude',
  selector: 'x-modal'
)
class ModalDec extends conditional.Conditional {
  ModalDec(ng.ViewFactory viewFactory, ng.ViewPort viewPort,
    ng.Scope scope) : super(viewFactory, viewPort, scope);

  void show(Function onSubmit, Function onCancel) {
    this.condition = true;

    var comp = utils.getDirective(this.element, modal.ModalComp);
    comp.submit = () {
      onSubmit(this.hide);
    };
    comp.cancel = () {
      onCancel(this.hide);
    };

    async.Timer.run(() {
      comp.state = true;
    });
  }

  async.Future hide() {
    var comp = utils.getDirective(this.element, modal.ModalComp);
    comp.state = false;
    return new async.Future.delayed(const Duration(milliseconds: 300), () {
      this.condition = false;
    });
  }
}
