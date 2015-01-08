library decorators;

import 'package:pritunl/decorators/noselect.dart' as noselect;
import 'package:pritunl/decorators/tooltip_attach.dart' as tooltip_attach;

import 'package:angular/angular.dart' as ng;

class DecoratorsMod extends ng.Module {
  DecoratorsMod() {
    this.bind(noselect.NoSelectDec);
    this.bind(tooltip_attach.TooltipAttachDec);
  }
}
