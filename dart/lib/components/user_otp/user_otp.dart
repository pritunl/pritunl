library user_otp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content;
import 'package:pritunl/models/user.dart' as user;

import 'package:angular/angular.dart' show Component, NgOneWayOneTime;

@Component(
  selector: 'user-otp',
  templateUrl: 'packages/pritunl/components/user_otp/user_otp.html',
  cssUrl: 'packages/pritunl/components/user_otp/user_otp.css'
)
class UserOtpComp extends modal_content.ModalContent {
  @NgOneWayOneTime('model')
  user.User model;

  String get qrcodeText {
    return 'otpauth://totp/${this.model.name}@'
      '${this.model.organizationName}?secret=${this.model.otpSecret}';
  }

  void reset() {
    this.clearFormError();
    this.clearAlert();
  }

  void newKey() {
    this.model.genNewOtp().then((_) {
      this.setAlert('Successfully generated new key.', 'success');
    });
  }
}
