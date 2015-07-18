library components;

import 'package:pritunl/components/alert/alert.dart'
  as alert;
import 'package:pritunl/components/alert_global/alert_global.dart'
  as alert_global;
import 'package:pritunl/components/box_label/box_label.dart'
  as box_label;
import 'package:pritunl/components/btn/btn.dart'
  as btn;
import 'package:pritunl/components/checkbox/checkbox.dart'
  as checkbox;
import 'package:pritunl/components/container/container.dart'
  as container;
import 'package:pritunl/components/editor/editor.dart'
  as editor;
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
import 'package:pritunl/components/navbar/navbar.dart'
  as navbar;
import 'package:pritunl/components/org_add/org_add.dart'
  as org_add;
import 'package:pritunl/components/org_del/org_del.dart'
  as org_del;
import 'package:pritunl/components/org_modify/org_modify.dart'
  as org_modify;
import 'package:pritunl/components/organization/organization.dart'
  as organization;
import 'package:pritunl/components/organizations/organizations.dart'
  as organizations;
import 'package:pritunl/components/qrcode/qrcode.dart'
  as qrcode;
import 'package:pritunl/components/server/server.dart'
  as server;
import 'package:pritunl/components/server_del/server_del.dart'
  as server_del;
import 'package:pritunl/components/servers/servers.dart'
  as servers;
import 'package:pritunl/components/status/status.dart'
  as status;
import 'package:pritunl/components/user/user.dart'
  as user;
import 'package:pritunl/components/user_add/user_add.dart'
  as user_add;
import 'package:pritunl/components/user_add_bulk/user_add_bulk.dart'
  as user_add_bulk;
import 'package:pritunl/components/user_del/user_del.dart'
  as user_del;
import 'package:pritunl/components/user_email/user_email.dart'
  as user_email;
import 'package:pritunl/components/user_key_links/user_key_links.dart'
  as user_key_links;
import 'package:pritunl/components/user_modify/user_modify.dart'
  as user_modify;
import 'package:pritunl/components/user_otp/user_otp.dart'
  as user_otp;

import 'package:angular/angular.dart' as ng;

class ComponentsMod extends ng.Module {
  ComponentsMod() {
    this.bind(alert.AlertComp);
    this.bind(alert_global.AlertGlobalComp);
    this.bind(box_label.BoxLabelComp);
    this.bind(btn.BtnComp);
    this.bind(checkbox.CheckboxComp);
    this.bind(container.ContainerComp);
    this.bind(editor.EditorComp);
    this.bind(form_group.FormGroupComp);
    this.bind(form_input.FormInputComp);
    this.bind(form_select.FormSelectComp);
    this.bind(form_textarea.FormTextareaComp);
    this.bind(fraction.FractionComp);
    this.bind(glyphicon.GlyphiconComp);
    this.bind(log_entries.LogEntriesComp);
    this.bind(modal.ModalComp);
    this.bind(navbar.NavbarComp);
    this.bind(org_add.OrgAddComp);
    this.bind(org_del.OrgDelComp);
    this.bind(org_modify.ModifyOrgComp);
    this.bind(organization.OrganizationComp);
    this.bind(organizations.OrganizationsComp);
    this.bind(qrcode.QrcodeComp);
    this.bind(server.ServerComp);
    this.bind(server_del.ServerDelComp);
    this.bind(servers.ServersComp);
    this.bind(status.StatusComp);
    this.bind(user.UserComp);
    this.bind(user_add.UserAddComp);
    this.bind(user_add_bulk.UserAddBulkComp);
    this.bind(user_del.UserDelComp);
    this.bind(user_email.UserEmailComp);
    this.bind(user_key_links.UserKeyLinksComp);
    this.bind(user_modify.UserModifyComp);
    this.bind(user_otp.UserOtpComp);
  }
}
