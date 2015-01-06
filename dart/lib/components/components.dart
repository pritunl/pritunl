library components;

import 'package:pritunl/components/box_label/box_label.dart'
as box_label;
import 'package:pritunl/components/btn/btn.dart'
as btn;
import 'package:pritunl/components/container/container.dart'
  as container;
import 'package:pritunl/components/fraction/fraction.dart'
  as fraction;
import 'package:pritunl/components/glyphicon/glyphicon.dart'
  as glyphicon;
import 'package:pritunl/components/log_entries/log_entries.dart'
  as log_entries;
import 'package:pritunl/components/navbar/navbar.dart'
  as navbar;
import 'package:pritunl/components/organization/organization.dart'
  as organization;
import 'package:pritunl/components/organizations/organizations.dart'
  as organizations;
import 'package:pritunl/components/rating/rating.dart'
  as rating;
import 'package:pritunl/components/status/status.dart'
  as status;
import 'package:pritunl/components/form_control/form_control.dart'
  as form_control;

import 'package:angular/angular.dart' as ng;

class ComponentsMod extends ng.Module {
  ComponentsMod() {
    this.bind(box_label.BoxLabelComp);
    this.bind(btn.BtnComp);
    this.bind(container.ContainerComp);
    this.bind(fraction.FractionComp);
    this.bind(glyphicon.GlyphiconComp);
    this.bind(log_entries.LogEntriesComp);
    this.bind(navbar.NavbarComp);
    this.bind(organization.OrganizationComp);
    this.bind(organizations.OrganizationsComp);
    this.bind(rating.RatingComp);
    this.bind(status.StatusComp);
    this.bind(form_control.FormControlComp);
  }
}
