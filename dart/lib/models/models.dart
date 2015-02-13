library models;

import 'package:pritunl/models/event.dart' as evnt;
import 'package:pritunl/models/key.dart' as ky;
import 'package:pritunl/models/log_entry.dart' as log_ent;
import 'package:pritunl/models/organization.dart' as organization;
import 'package:pritunl/models/server.dart' as server;
import 'package:pritunl/models/server_output.dart' as svr_output;
import 'package:pritunl/models/status.dart' as stus;
import 'package:pritunl/models/user.dart' as usr;

import 'package:angular/angular.dart' as ng;

class ModelsMod extends ng.Module {
  ModelsMod() {
    this.bind(evnt.Event);
    this.bind(ky.Key);
    this.bind(log_ent.LogEntry);
    this.bind(organization.Organization);
    this.bind(server.Server);
    this.bind(svr_output.ServerOutput);
    this.bind(stus.Status);
    this.bind(usr.User);
  }
}
