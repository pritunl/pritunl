library decorators;

import 'package:pritunl/decorators/autofocus.dart' as autofocus;
import 'package:pritunl/decorators/modal.dart' as modal;
import 'package:pritunl/decorators/modal_attach.dart' as modal_attach;
import 'package:pritunl/decorators/noselect.dart' as noselect;
import 'package:pritunl/decorators/shift_click.dart' as shift_click;
import 'package:pritunl/decorators/tooltip.dart' as tooltip;

import 'package:angular/angular.dart' as ng;

class DecoratorsMod extends ng.Module {
  DecoratorsMod() {
    this.bind(autofocus.AutoFocusDec);
    this.bind(modal.ModalDec);
    this.bind(modal_attach.ModalAttachDec);
    this.bind(noselect.NoSelectDec);
    this.bind(shift_click.ShiftClickDec);
    this.bind(tooltip.TooltipDec);
  }
}
