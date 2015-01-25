library components;

import 'package:pritunl/components/add_org/add_org.dart'
  as add_org;
import 'package:pritunl/components/add_user/add_user.dart'
  as add_user;
import 'package:pritunl/components/add_user_bulk/add_user_bulk.dart'
  as add_user_bulk;
import 'package:pritunl/components/alert/alert.dart'
  as alert;
import 'package:pritunl/components/box_label/box_label.dart'
  as box_label;
import 'package:pritunl/components/btn/btn.dart'
  as btn;
import 'package:pritunl/components/checkbox/checkbox.dart'
  as checkbox;
import 'package:pritunl/components/container/container.dart'
  as container;
import 'package:pritunl/components/del_org/del_org.dart'
  as del_org;
import 'package:pritunl/components/form_group/form_group.dart'
  as form_group;
import 'package:pritunl/components/form_input/form_input.dart'
  as form_input;
import 'package:pritunl/components/form_select/form_select.dart'
  as form_select;
import 'package:pritunl/components/form_textarea/form_textarea.dart'
  as form_textarea;
import 'package:pritunl/components/fraction/fraction.dart'
  as fraction;
import 'package:pritunl/components/glyphicon/glyphicon.dart'
  as glyphicon;
import 'package:pritunl/components/log_entries/log_entries.dart'
  as log_entries;
import 'package:pritunl/components/modal/modal.dart'
  as modal;
import 'package:pritunl/components/modify_org/modify_org.dart'
  as modify_org;
import 'package:pritunl/components/modify_user/modify_user.dart'
  as modify_user;
import 'package:pritunl/components/navbar/navbar.dart'
  as navbar;
import 'package:pritunl/components/organization/organization.dart'
  as organization;
import 'package:pritunl/components/organizations/organizations.dart'
  as organizations;
import 'package:pritunl/components/status/status.dart'
  as status;
import 'package:pritunl/components/user/user.dart'
  as user;

import 'package:angular/angular.dart' as ng;

class ComponentsMod extends ng.Module {
  ComponentsMod() {
    this.bind(add_org.AddOrgComp);
    this.bind(add_user.AddUserComp);
    this.bind(add_user_bulk.AddUserBulkComp);
    this.bind(alert.AlertComp);
    this.bind(box_label.BoxLabelComp);
    this.bind(btn.BtnComp);
    this.bind(checkbox.CheckboxComp);
    this.bind(container.ContainerComp);
    this.bind(del_org.DelOrgComp);
    this.bind(form_group.FormGroupComp);
    this.bind(form_input.FormInputComp);
    this.bind(form_select.FormSelectComp);
    this.bind(form_textarea.FormTextareaComp);
    this.bind(fraction.FractionComp);
    this.bind(glyphicon.GlyphiconComp);
    this.bind(log_entries.LogEntriesComp);
    this.bind(modal.ModalComp);
    this.bind(modify_org.ModifyOrgComp);
    this.bind(modify_user.ModifyUserComp);
    this.bind(navbar.NavbarComp);
    this.bind(organization.OrganizationComp);
    this.bind(organizations.OrganizationsComp);
    this.bind(status.StatusComp);
    this.bind(user.UserComp);
  }
}
