library capitalize_form;

import 'package:angular/angular.dart' show Formatter;

@Formatter(name: 'capitalize')
class CapitalizeForm {
  String call(String input) {
    if (input == null) {
      return null;
    }

    if (input.length < 1) {
      return input;
    }

    return input.substring(0, 1).toUpperCase() + input.substring(1);
  }
}
