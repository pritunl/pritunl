library qrcode_comp;

import 'package:pritunl/all_aware.dart' as all_aware;

import 'package:angular/angular.dart' show Component, NgAttr, NgOneWay,
  NgOneWayOneTime;
import 'dart:html' as dom;
import 'dart:async' as async;
import 'dart:js' as js;

@Component(
  selector: 'x-qrcode',
  template: '<div></div>'
)
class QrcodeComp extends all_aware.AllAware {
  dom.Element qrcodeElem;
  var _curText;
  var _attached;

  var _text;
  @NgOneWay('text')
  void set text(String val) {
    this._text = val;
    if (this._attached == true) {
      this.buildQrcode();
    }
  }
  String get text {
    return this._text;
  }

  @NgOneWayOneTime('width')
  int width;

  @NgOneWayOneTime('height')
  int height;

  void buildQrcode() {
    if (this._curText == this.text) {
      return;
    }
    this._curText = this.text;
    var qrcodeElem = new dom.Element.div();
    var qrSettings = new js.JsObject.jsify({
      'text': this._curText,
      'width': this.width,
      'height': this.height,
      'colorDark': '#3276b1',
      'colorLight': '#fff'
    });

    new js.JsObject(js.context['QRCode'], [qrcodeElem, qrSettings]);

    qrcodeElem.querySelector('canvas').style.margin = '0 auto';
    qrcodeElem.querySelector('img').style.margin = '0 auto';

    new async.Timer(const Duration(milliseconds: 50), () {
      this.qrcodeElem.replaceWith(qrcodeElem);
      this.qrcodeElem = qrcodeElem;
    });
  }

  void onAll(dom.ShadowRoot root) {
    this.qrcodeElem = root.querySelector('div');
    this.buildQrcode();
    this._attached = true;
  }
}
