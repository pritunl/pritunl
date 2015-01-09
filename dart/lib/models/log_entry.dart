library log_entry;

import 'package:pritunl/model.dart' as model;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class LogEntry extends model.Model {
  var id;
  var timestamp;
  var message;

  LogEntry(ng.Http http) : super(http);
}
