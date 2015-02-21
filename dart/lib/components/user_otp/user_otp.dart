library user_otp_comp;

import 'package:pritunl/bases/modal_content/modal_content.dart' as
  modal_content_base;
import 'package:pritunl/models/user.dart' as usr;

import 'package:angular/angular.dart' show Component, NgOneWayOneTime;

@Component(
  selector: 'x-user-otp',
  templateUrl: 'packages/pritunl/components/user_otp/user_otp.html',
  cssUrl: 'packages/pritunl/components/user_otp/user_otp.css'
)
class UserOtpComp extends modal_content_base.ModalContent {
  @NgOneWayOneTime('model')
  usr.User model;
  bool genKeyDisabled;

  String get qrcodeText {
    return 'otpauth://totp/${this.model.name}@'
      '${this.model.organizationName}?secret=${this.model.otpSecret}';
  }

  void reset() {
    this.clearFormError();
    this.clearAlert();
  }

  void newKey() {
    this.genKeyDisabled = true;

    this.model.genNewOtp().then((_) {
      this.setAlert('Successfully generated new key.', 'success');
    }).catchError((err) {
      this.setAlert('Failed to generate new key, server error occurred.',
        'danger');
    }).whenComplete(() {
      this.genKeyDisabled = false;
    });
  }
}
