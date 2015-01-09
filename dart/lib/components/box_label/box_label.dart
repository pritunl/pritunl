library box_label;

import 'package:angular/angular.dart' show Component, NgAttr;
import 'package:angular/angular.dart' as ng;

@Component(
  selector: 'box-label',
  template: '<span ng-class="type"><content></content></span>',
  cssUrl: 'packages/pritunl/components/box_label/box_label.css'
)
class BoxLabelComp implements ng.ShadowRootAware {
  @NgAttr('padding')
  var padding;

  @NgAttr('type')
  var type;

  onShadowRoot(root) {
    if (this.padding != null) {
      root.querySelector('span').style.padding = this.padding;
    }
  }
}
