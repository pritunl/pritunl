library collections;

import 'package:pritunl/collections/log_entries.dart' as log_entries;

import 'package:angular/angular.dart' as ng;

class CollectionsMod extends ng.Module {
  CollectionsMod() {
    this.bind(log_entries.LogEntries);
  }
}
