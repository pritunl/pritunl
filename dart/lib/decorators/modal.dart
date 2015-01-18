library modal;

import 'package:pritunl/decorators/conditional.dart' as conditional;
import 'package:pritunl/utils/utils.dart' as utils;
import 'package:pritunl/components/modal/modal.dart' as modal;

import 'package:angular/angular.dart' show Decorator;
import 'package:angular/angular.dart' as ng;

@Decorator(
  children: 'transclude',
  selector: 'modal'
)
class ModalDec extends conditional.Conditional {
  ModalDec(ng.ViewFactory viewFactory, ng.ViewPort viewPort,
    ng.Scope scope) : super(viewFactory, viewPort, scope);

  void show(Function onSubmit, Function onCancel) {
    this.condition = true;

    var comp = utils.getDirective(this.element, modal.ModalComp);
    comp.submit = () {
      if (onSubmit() == false) {
        return;
      }
      this.hide();
    };
    comp.cancel = () {
      if (onCancel() == false) {
        return;
      }
      this.hide();
    };

    comp.state = true;
  }

  void hide() {
    var comp = utils.getDirective(this.element, modal.ModalComp);
    comp.state = false;
  }
}
