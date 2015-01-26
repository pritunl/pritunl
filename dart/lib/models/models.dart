library models;

import 'package:pritunl/models/key.dart' as key;
import 'package:pritunl/models/log_entry.dart' as log_entry;
import 'package:pritunl/models/organization.dart' as organization;
import 'package:pritunl/models/status.dart' as status;
import 'package:pritunl/models/user.dart' as user;

import 'package:angular/angular.dart' as ng;

class ModelsMod extends ng.Module {
  ModelsMod() {
    this.bind(key.Key);
    this.bind(log_entry.LogEntry);
    this.bind(organization.Organization);
    this.bind(status.Status);
    this.bind(user.User);
  }
}
