library log_entries_comp;

import 'package:pritunl/collections/log_entries.dart' as log_ents;

import 'package:angular/angular.dart' show Component;

@Component(
  selector: 'x-log-entries',
  templateUrl: 'packages/pritunl/components/log_entries/log_entries.html',
  cssUrl: 'packages/pritunl/components/log_entries/log_entries.css'
)
class LogEntriesComp {
  log_ents.LogEntries entries;

  LogEntriesComp(this.entries) {
    this.update();
  }

  void update() {
    this.entries.fetch();
  }
}
