library datetime_form;

import 'package:angular/angular.dart' show Formatter;

@Formatter(name: 'datetime')
class DatetimeForm {
  String call(int time) {
    if (time == null) {
      return null;
    }

    var date = new DateTime.fromMillisecondsSinceEpoch(time * 1000);

    var abbrev = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    var month = abbrev[date.month - 1];

    var day = date.day.toString();

    var year = date.year;

    var meridiem;
    var hour = date.hour;
    if (hour > 12) {
      meridiem = 'pm';
      hour = (hour - 12).toString();
    }
    else {
      meridiem = 'am';
      hour = hour.toString();
    }

    var minute = date.minute.toString();
    if (minute.length < 2) {
      minute = '0$minute';
    }

    return '$hour:$minute $meridiem - $month $day $year';
  }
}
