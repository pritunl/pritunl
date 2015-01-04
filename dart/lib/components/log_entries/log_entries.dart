library log_entries;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;
import 'package:angular/angular.dart' as ng;

@Component(
  selector: 'log-entries',
  templateUrl: 'packages/pritunl/components/log_entries/log_entries.html',
  cssUrl: 'packages/pritunl/components/log_entries/log_entries.css'
)
class LogEntriesComp {
  var http;
  var entries;

  LogEntriesComp(ng.Http this.http) {
    this.update();
  }

  update() {
    this.http.get('/log').then((response) {
      this.entries = response.data;
    });
  }
}
