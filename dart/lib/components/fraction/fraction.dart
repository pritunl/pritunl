library fraction;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;

var DEFAULT_NULL_STYLE = 'default';
var DEFAULT_EMPTY_STYLE = 'danger';
var DEFAULT_HALF_STYLE = 'warning';
var DEFAULT_FULL_STYLE = 'success';

@Component(
  selector: 'fraction',
  template: '<span ng-class="colorType">{{numer}}/{{denom}}</span>',
  cssUrl: 'packages/pritunl/components/fraction/fraction.css'
)
class FractionComp {
  @NgAttr('numer')
  var numer;

  @NgAttr('denom')
  var denom;

  @NgAttr('null-style')
  var nullStyle;

  @NgAttr('empty-style')
  var emptyStyle;

  @NgAttr('half-style')
  var halfStyle;

  @NgAttr('full-style')
  var fullStyle;

  get numerInt {
    if (this.numer == null) {
      return null;
    }
    try {
      return int.parse(this.numer);
    } on FormatException catch(err) {
      return null;
    }
  }

  get denomInt {
    if (this.denom == null) {
      return null;
    }
    try {
      return int.parse(this.denom);
    } on FormatException catch(err) {
      return null;
    }
  }

  get colorType {
    var numerInt = this.numerInt;
    var denomInt = this.denomInt;

    if (numerInt == null || denomInt == null) {
      if (this.nullStyle == null) {
        return DEFAULT_NULL_STYLE;
      }
      return this.nullStyle;
    }

    if (numerInt == denomInt) {
      if (this.fullStyle == null) {
        return DEFAULT_FULL_STYLE;
      }
      return this.fullStyle;
    }
    else if (numerInt == 0) {
      if (this.emptyStyle == null) {
        return DEFAULT_EMPTY_STYLE;
      }
      return this.emptyStyle;
    }

    if (this.halfStyle == null) {
      return DEFAULT_HALF_STYLE;
    }
    return this.halfStyle;
  }
}
