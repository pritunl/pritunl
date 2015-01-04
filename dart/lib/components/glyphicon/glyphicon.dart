library glyphicon;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;

@Component(
  selector: 'glyphicon',
  template: '<span ng-class="iconClass"></span>',
  cssUrl: 'packages/pritunl/components/glyphicon/glyphicon.css'
)
class GlyphiconComp {
  @NgAttr('icon-type')
  var iconType;
}
