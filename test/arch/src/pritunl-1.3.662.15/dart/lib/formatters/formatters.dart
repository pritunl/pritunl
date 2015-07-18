library formatters;

import 'package:pritunl/formatters/capitalize.dart' as capitalize;
import 'package:pritunl/formatters/datetime.dart' as datetime;
import 'package:pritunl/formatters/fraction.dart' as fraction;
import 'package:pritunl/formatters/slash.dart' as slash;
import 'package:pritunl/formatters/timer.dart' as timer;

import 'package:angular/angular.dart' as ng;

class FormattersMod extends ng.Module {
  FormattersMod() {
    this.bind(capitalize.CapitalizeForm);
    this.bind(datetime.DatetimeForm);
    this.bind(fraction.FractionForm);
    this.bind(slash.SlashForm);
    this.bind(timer.TimerForm);
  }
}
