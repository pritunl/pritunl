library log_entry;

import 'package:pritunl/model.dart' as model;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class LogEntry extends model.Model {
  @model.Attribute('id')
  String id;

  @model.Attribute('timestamp')
  int timestamp;

  @model.Attribute('message')
  String message;

  LogEntry(ng.Http http) : super(http);
}
