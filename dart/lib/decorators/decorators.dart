library decorators;

import 'package:pritunl/decorators/autofocus.dart' as autofocus;
import 'package:pritunl/decorators/noselect.dart' as noselect;
import 'package:pritunl/decorators/shift_click.dart' as shift_click;
import 'package:pritunl/decorators/tooltip_attach.dart' as tooltip_attach;

import 'package:angular/angular.dart' as ng;

class DecoratorsMod extends ng.Module {
  DecoratorsMod() {
    this.bind(autofocus.AutoFocusDec);
    this.bind(noselect.NoSelectDec);
    this.bind(shift_click.ShiftClickDec);
    this.bind(tooltip_attach.TooltipAttachDec);
  }
}
