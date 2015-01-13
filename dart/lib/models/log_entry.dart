library log_entry;

import 'package:pritunl/model.dart' as model;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class LogEntry extends model.Model {
  @model.Attr('id')
  var id;

  @model.Attr('timestamp')
  var timestamp;

  @model.Attr('message')
  var message;

  LogEntry(ng.Http http) : super(http);
}
