library decorators;

import 'package:pritunl/decorators/noselect.dart' as noselect;

import 'package:angular/angular.dart' as ng;

class DecoratorsMod extends ng.Module {
  DecoratorsMod() {
    this.bind(noselect.NoSelectDec);
  }
}
