library box_label;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;
import 'package:angular/angular.dart' as ng;

@Component(
  selector: 'box-label',
  template: '<span ng-class="type"><content></content></span>',
  cssUrl: 'packages/pritunl/components/box_label/box_label.css'
)
class BoxLabelComp implements ng.ShadowRootAware {
  @NgAttr('type')
  var type;

  @NgAttr('padding')
  var padding;

  onShadowRoot(root) {
    var spanElem = root.querySelector('span');

    if (this.padding != null) {
      spanElem.style.padding = this.padding;
    }
  }
}
