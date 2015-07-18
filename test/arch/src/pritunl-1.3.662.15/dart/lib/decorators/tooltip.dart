library tooltip_attach_dec;

import 'package:angular/angular.dart' show NgAttr, Decorator;
import 'dart:html' as dom;
import 'dart:async' as async;

@Decorator(
  selector: '[tooltip]'
)
class TooltipDec {
  dom.Element element;
  dom.Element tooltipElem;

  var _tooltip;
  @NgAttr('tooltip')
  get tooltip {
    return this._tooltip;
  }
  void set tooltip(val) {
    this._tooltip = val;
    if (this.tooltipElem != null) {
      this.hide().then((_) {
        this.show();
      });
    }
  }

  TooltipDec(this.element) {
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

  void show() {
    if (this.tooltipElem != null) {
      return;
    }
    if (this.tooltip == null || this.tooltip == '') {
      return;
    }

    this.tooltipElem = new dom.DivElement();
    var inner = new dom.DivElement();
    var arrow = new dom.DivElement();

    this.tooltipElem.append(inner);
    this.tooltipElem.append(arrow);
    inner.appendText(this.tooltip);

    this.tooltipElem.style
      ..position = 'absolute'
      ..display = 'inline-block'
      ..zIndex = '1070'
      ..fontSize = '12px'
      ..lineHeight = '1.4'
      ..maxWidth = '200px'
      ..padding = '3px 8px'
      ..color = '#fff'
      ..backgroundColor = '#000'
      ..borderRadius = '2px'
      ..opacity = '0'
      ..transition = 'opacity .15s linear';

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

    this.element.insertAdjacentElement('beforeBegin', this.tooltipElem);

    var x = this.element.offsetLeft + this.element.offsetWidth / 2 -
      this.tooltipElem.offsetWidth / 2;
    var y = this.element.offsetTop - this.tooltipElem.offsetHeight - 5;

    this.tooltipElem.style
      ..left = '${x}px'
      ..top = '${y}px'
      ..opacity = '1';
  }

  async.Future hide() {
    if (this.tooltipElem == null) {
      return null;
    }

    this.tooltipElem.style.opacity = '0';
    return new async.Future.delayed(const Duration(milliseconds: 150), () {
      if (this.tooltipElem == null) {
        return;
      }

      this.tooltipElem.remove();
      this.tooltipElem = null;
    });
  }
}
