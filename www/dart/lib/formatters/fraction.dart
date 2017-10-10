library fraction_form;

import 'package:angular/angular.dart' show Formatter;

@Formatter(name: 'fraction')
class FractionForm {
  String call(List<int> input) {
    if (input[0] == null || input[1] == null || (
        input[0] == 0 && input[1] == 0)) {
      return '-/-';
    }
    return '${input[0]}/${input[1]}';
  }
}
