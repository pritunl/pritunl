library formatters;

import 'package:pritunl/formatters/datetime.dart' as datetime;

import 'package:angular/angular.dart' as ng;

class FormattersMod extends ng.Module {
  FormattersMod() {
    this.bind(datetime.DatetimeForm);
  }
}
