library slash_form;

import 'package:angular/angular.dart' show Formatter;

@Formatter(name: 'slash')
class SlashForm {
  dynamic call(dynamic input) {
    if (input == null) {
      return '-';
    }
    return input;
  }
}
