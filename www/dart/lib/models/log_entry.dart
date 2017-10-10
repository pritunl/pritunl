library log_entry_mod;

import 'package:pritunl/model.dart' as mdl;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class LogEntry extends mdl.Model {
  @mdl.Attribute('id')
  String id;

  @mdl.Attribute('timestamp')
  int timestamp;

  @mdl.Attribute('message')
  String message;

  LogEntry(ng.Http http) : super(http);
}
