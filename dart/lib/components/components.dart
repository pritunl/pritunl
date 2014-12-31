library components;

import 'package:pritunl/components/status/status.dart' as status;
import 'package:pritunl/components/rating/rating.dart' as rating;

import 'package:angular/angular.dart' as ng;

class ComponentsMod extends ng.Module {
  ComponentsMod() {
    this.bind(rating.RatingComp);
    this.bind(status.StatusComp);
  }
}
