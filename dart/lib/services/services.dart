library services;

import 'package:pritunl/services/builder.dart' as builder;

import 'package:angular/angular.dart' as ng;

class ServicesMod extends ng.Module {
  ServicesMod() {
    this.bind(builder.BuilderServ);
  }
}
