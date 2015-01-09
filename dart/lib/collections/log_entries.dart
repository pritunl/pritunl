library model;

import 'package:pritunl/collection.dart' as collection;
import 'package:pritunl/models/log_entry.dart' as log_entry;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class LogEntries extends collection.Collection {
  var model = log_entry.LogEntry;

  get url {
    return '/log';
  }

  LogEntries(ng.Http http) : super(http);
}
