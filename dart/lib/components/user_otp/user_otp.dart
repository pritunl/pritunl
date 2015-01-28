library user_otp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content;
import 'package:pritunl/models/user.dart' as user;

import 'package:angular/angular.dart' show Component, NgOneWayOneTime;
import 'package:angular/angular.dart' as ng;
import 'dart:html' as dom;

@Component(
  selector: 'user-otp',
  templateUrl: 'packages/pritunl/components/user_otp/user_otp.html',
  cssUrl: 'packages/pritunl/components/user_otp/user_otp.css'
)
class UserOtpComp extends modal_content.ModalContent implements
    ng.ShadowRootAware {
  @NgOneWayOneTime('model')
  user.User model;

  void onShadowRoot(dom.ShadowRoot root) {

  }
}
