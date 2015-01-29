library checkbox_comp;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgCallback;
import 'dart:html' as dom;

@Component(
  selector: 'checkbox',
  template: r'<div ng-click="onClick($event)">'
    '<glyphicon type="ok" ng-if="state"></glyphicon></div>',
  cssUrl: 'packages/pritunl/components/checkbox/checkbox.css'
)
class CheckboxComp {
  @NgTwoWay('state')
  bool state;

  @NgCallback('on-select')
  Function onSelect;

  void onClick(dom.MouseEvent evt) {
    if (this.onSelect != null) {
      this.onSelect({r'$shift': evt.shiftKey});
    }
    else {
      this.state = this.state != true;
    }
  }
}
