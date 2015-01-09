library model;

import 'package:pritunl/models/status.dart' as status;

import 'package:angular/angular.dart' as ng;

class ModelsMod extends ng.Module {
  ModelsMod() {
    this.bind(status.Status);
  }
}
