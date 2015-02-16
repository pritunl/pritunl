library timer_form;

import 'package:angular/angular.dart' show Formatter;

@Formatter(name: 'timer')
class TimerForm {
  String call(int count) {
    if (count == null || count == 0) {
      return '-';
    }

    var days = (count / 86400).floor();
    count -= days * 86400;

    var hours = (count / 3600).floor();
    count -= hours * 3600;

    var mins = (count / 60).floor();
    count -= mins * 60;

    if (days > 0) {
      return '${days}d ${hours}h ${mins}m ${count}s';
    }
    else if (hours > 0) {
      return '${hours}h ${mins}m ${count}s';
    }
    else if (mins > 0) {
      return '${mins}m ${count}s';
    }
    else {
      return '${count}s';
    }
  }
}
