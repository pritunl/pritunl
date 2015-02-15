library collections;

import 'package:pritunl/collections/events.dart' as evnts;
import 'package:pritunl/collections/log_entries.dart' as log_ents;
import 'package:pritunl/collections/organizations.dart' as organizations;
import 'package:pritunl/collections/server_hosts.dart' as svr_hsts;
import 'package:pritunl/collections/server_orgs.dart' as svr_orgs;
import 'package:pritunl/collections/servers.dart' as svrs;
import 'package:pritunl/collections/users.dart' as usrs;

import 'package:angular/angular.dart' as ng;

class CollectionsMod extends ng.Module {
  CollectionsMod() {
    this.bind(evnts.Events);
    this.bind(log_ents.LogEntries);
    this.bind(organizations.Organizations);
    this.bind(svr_hsts.ServerHosts);
    this.bind(svr_orgs.ServerOrgs);
    this.bind(svrs.Servers);
    this.bind(usrs.Users);
  }
}
