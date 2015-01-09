library models;

import 'package:pritunl/models/log_entry.dart' as log_entry;
import 'package:pritunl/models/status.dart' as status;

import 'package:angular/angular.dart' as ng;

class ModelsMod extends ng.Module {
  ModelsMod() {
    this.bind(log_entry.LogEntry);
    this.bind(status.Status);
  }
}
