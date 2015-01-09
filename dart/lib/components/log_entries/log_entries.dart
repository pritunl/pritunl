library log_entries;

import 'package:pritunl/collections/log_entries.dart' as log_entries;

import 'package:angular/angular.dart' show Component;
import 'package:angular/angular.dart' as ng;

@Component(
  selector: 'log-entries',
  templateUrl: 'packages/pritunl/components/log_entries/log_entries.html',
  cssUrl: 'packages/pritunl/components/log_entries/log_entries.css'
)
class LogEntriesComp {
  var http;
  var entries;

  LogEntriesComp(ng.Http this.http, log_entries.LogEntries this.entries) {
    this.update();
  }

  update() {
    this.entries.fetch();
  }
}
