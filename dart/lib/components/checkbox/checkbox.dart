library checkbox_comp;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgCallback;

@Component(
  selector: 'checkbox',
  template: '<div ng-click="onClick()">'
    '<glyphicon type="ok" ng-if="state"></glyphicon></div>',
  cssUrl: 'packages/pritunl/components/checkbox/checkbox.css'
)
class CheckboxComp {
  @NgTwoWay('state')
  bool state;

  @NgCallback('on-select')
  Function onSelect;

  void onClick() {
    if (this.onSelect != null) {
      this.onSelect();
    }
    else {
      this.state = this.state != true;
    }
  }
}
