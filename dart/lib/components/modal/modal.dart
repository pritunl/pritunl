library modal;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;

@Component(
  selector: 'modal',
  templateUrl: 'packages/pritunl/components/modal/modal.html',
  cssUrl: 'packages/pritunl/components/modal/modal.css'
)
class ModalComp {
  var state;

  ModalComp() {
  }

  open() {
    this.state = true;
  }

  close() {
    this.state = false;
  }

  softClose(target) {
    if (target.classes.contains('modal')) {
      this.close();
    }
  }

  hardClose() {
    print('hardClose');
    this.close();
  }

  submit() {
    print('submit');
    this.close();
  }
}
