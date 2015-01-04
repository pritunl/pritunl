library components;

import 'package:pritunl/components/box_label/box_label.dart' as box_label;
import 'package:pritunl/components/navbar/navbar.dart' as navbar;
import 'package:pritunl/components/status/status.dart' as status;
import 'package:pritunl/components/rating/rating.dart' as rating;
import 'package:pritunl/components/fraction/fraction.dart' as fraction;
import 'package:pritunl/components/glyphicon/glyphicon.dart' as glyphicon;

import 'package:angular/angular.dart' as ng;

class ComponentsMod extends ng.Module {
  ComponentsMod() {
    this.bind(box_label.BoxLabelComp);
    this.bind(navbar.NavbarComp);
    this.bind(rating.RatingComp);
    this.bind(status.StatusComp);
    this.bind(fraction.FractionComp);
    this.bind(glyphicon.GlyphiconComp);
  }
}
