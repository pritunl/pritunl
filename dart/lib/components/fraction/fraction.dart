library fraction_comp;

import 'package:angular/angular.dart' show Component, NgAttr;

const String DEFAULT_NULL_STYLE = 'default';
const String DEFAULT_EMPTY_STYLE = 'danger';
const String DEFAULT_HALF_STYLE = 'warning';
const String DEFAULT_FULL_STYLE = 'success';

@Component(
  selector: 'x-fraction',
  template: '<span ng-class="colorType">{{numerStr}}/{{denomStr}}</span>',
  cssUrl: 'packages/pritunl/components/fraction/fraction.css'
)
class FractionComp {
  @NgAttr('numer')
  String numer;

  @NgAttr('denom')
  String denom;

  @NgAttr('null-style')
  String nullStyle;

  @NgAttr('empty-style')
  String emptyStyle;

  @NgAttr('half-style')
  String halfStyle;

  @NgAttr('full-style')
  String fullStyle;

  String get numerStr {
    if (this.numer != null) {
      try {
        int.parse(this.numer);
        return this.numer;
      } on FormatException catch(_) {
      }
    }
    return '-';
  }

  String get denomStr {
    if (this.denom != null) {
      try {
        int.parse(this.denom);
        return this.denom;
      } on FormatException catch(_) {
      }
    }
    return '-';
  }

  int get numerInt {
    if (this.numer == null) {
      return null;
    }
    try {
      return int.parse(this.numer);
    } on FormatException catch(_) {
      return null;
    }
  }

  int get denomInt {
    if (this.denom == null) {
      return null;
    }
    try {
      return int.parse(this.denom);
    } on FormatException catch(_) {
      return null;
    }
  }

  String get colorType {
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
