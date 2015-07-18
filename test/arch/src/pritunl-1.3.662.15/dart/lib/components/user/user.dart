library user_comp;

import 'package:pritunl/models/user.dart' as usr;

import 'package:angular/angular.dart' show Component, NgOneWay, NgTwoWay,
  NgCallback;
import 'dart:html' as dom;

@Component(
  selector: 'x-user',
  templateUrl: 'packages/pritunl/components/user/user.html',
  cssUrl: 'packages/pritunl/components/user/user.css'
)
class UserComp {
  @NgOneWay('model')
  usr.User model;

  @NgOneWay('show-hidden')
  bool showHidden;

  @NgOneWay('selected')
  bool selected;

  @NgCallback('on-select')
  Function onSelect;

  @NgTwoWay('show-servers')
  bool showServers;

  String get statusIcon {
    if (this.model.disabled == true) {
      return 'disabled';
    }
    else if (this.model.status == true) {
      return 'online';
    }
    return 'offline';
  }

  String get statusText {
    if (this.model.disabled == true) {
      return 'Disabled';
    }
    else if (this.model.status == true) {
      return 'Online';
    }
    return 'Offline';
  }

  void toggleDisabled(dom.Event evt) {
    dom.Element target = evt.target;

    if (target.classes.contains('disabled')) {
      return;
    }
    target.classes.add('disabled');

    var model = this.model.clone();
    model.disabled = this.model.disabled != true;
    model.save(['disabled']).then((_) {
      this.model.disabled = model.disabled;
      target.classes.remove('disabled');
    });
  }
}
