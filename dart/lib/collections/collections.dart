library collections;

import 'package:pritunl/collections/events.dart' as events;
import 'package:pritunl/collections/log_entries.dart' as log_entries;
import 'package:pritunl/collections/organizations.dart' as organizations;
import 'package:pritunl/collections/users.dart' as users;

import 'package:angular/angular.dart' as ng;

class CollectionsMod extends ng.Module {
  CollectionsMod() {
    this.bind(events.Events);
    this.bind(log_entries.LogEntries);
    this.bind(organizations.Organizations);
    this.bind(users.Users);
  }
}
