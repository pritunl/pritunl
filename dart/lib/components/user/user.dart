library user_comp;

import 'package:pritunl/models/user.dart' as user;

import 'package:angular/angular.dart' show Component, NgOneWay, NgTwoWay,
  NgCallback;
import 'dart:html' as dom;

@Component(
  selector: 'user',
  templateUrl: 'packages/pritunl/components/user/user.html',
  cssUrl: 'packages/pritunl/components/user/user.css'
)
class UserComp {
  @NgOneWay('model')
  user.User model;

  @NgOneWay('show-hidden')
  bool showHidden;

  @NgTwoWay('selected')
  bool selected;

  @NgTwoWay('show-servers')
  bool showServers;

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
