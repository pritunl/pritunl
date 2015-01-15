library tooltip_attach;

import 'package:angular/angular.dart' show NgAttr, Decorator;
import 'dart:html' as dom;

@Decorator(
  selector: '[tooltip]'
)
class TooltipDec {
  var element;
  var tooltipElement;

  @NgAttr('tooltip')
  var tooltip;

  show() {
    if (this.tooltipElement != null) {
      return;
    }
    if (this.tooltip == null || this.tooltip == '') {
      return;
    }

    this.tooltipElement = new dom.DivElement();
    var inner = new dom.DivElement();
    var arrow = new dom.DivElement();

    this.tooltipElement.append(inner);
    this.tooltipElement.append(arrow);
    inner.appendText(this.tooltip);

    this.tooltipElement.style
      ..position = 'absolute'
      ..display = 'inline-block'
      ..zIndex = '1070'
      ..fontSize = '12px'
      ..lineHeight = '1.4'
      ..maxWidth = '200px'
      ..padding = '3px 8px'
      ..color = '#fff'
      ..backgroundColor = '#000'
      ..borderRadius = '2px';

    arrow.style
      ..position = 'absolute'
      ..width = '0'
      ..height = '0'
      ..borderColor = 'rgba(0, 0, 0, 0)'
      ..borderStyle = 'solid'
      ..borderWidth = '5px 5px 0'
      ..borderTopColor = '#000'
      ..left = '50%'
      ..marginTop = '2px'
      ..marginLeft = '-5px';

    this.element.insertAdjacentElement('beforeBegin', this.tooltipElement);

    var bounds = this.element.getBoundingClientRect();
    var tooltipBounds = this.tooltipElement.getBoundingClientRect();
    var x = bounds.left + bounds.width / 2 - tooltipBounds.width / 2;
    var y = bounds.top - tooltipBounds.height - 5;

    this.tooltipElement.style
      ..left = '${x}px'
      ..top = '${y}px';
  }

  hide() {
    this.tooltipElement.remove();
    this.tooltipElement = null;
  }

  TooltipDec(dom.Element this.element) {
    this.element
      ..onMouseEnter.listen((_) {
        this.show();
      })
      ..onMouseOver.listen((_) {
        this.show();
      })
      ..onMouseLeave.listen((_) {
        this.hide();
      });
  }
}
