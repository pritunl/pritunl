library log_entries_col;

import 'package:pritunl/collection.dart' as collec;
import 'package:pritunl/models/log_entry.dart' as log_ent;

import 'package:angular/angular.dart' show Injectable;
import 'package:angular/angular.dart' as ng;

@Injectable()
class LogEntries extends collec.Collection {
  Type model = log_ent.LogEntry;

  LogEntries(ng.Http http) : super(http);

  String get url {
    return '/log';
  }
}
