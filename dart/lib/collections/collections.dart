library collections;

import 'package:pritunl/collections/events.dart' as evnts;
import 'package:pritunl/collections/log_entries.dart' as log_ents;
import 'package:pritunl/collections/organizations.dart' as organizations;
import 'package:pritunl/collections/users.dart' as usrs;

import 'package:angular/angular.dart' as ng;

class CollectionsMod extends ng.Module {
  CollectionsMod() {
    this.bind(evnts.Events);
    this.bind(log_ents.LogEntries);
    this.bind(organizations.Organizations);
    this.bind(usrs.Users);
  }
}
