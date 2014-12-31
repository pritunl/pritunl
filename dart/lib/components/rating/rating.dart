library rating;

import 'package:angular/angular.dart' show Component, NgTwoWay, NgAttr;

var STAR_ON_CHAR = '\u2605';
var STAR_OFF_CHAR = '\u2606';
var STAR_ON_CLASS = 'star-on';
var STAR_OFF_CLASS = 'star-off';
var DEFAULT_MAX = 5;

@Component(
    selector: 'rating',
    templateUrl: 'packages/pritunl/components/rating/rating.html',
    cssUrl: 'rating.css'
)
class RatingComp {
  var stars = [];

  @NgTwoWay('rating')
  var rating;

  @NgAttr('max-rating')
  set maxRating(value) {
    var count;

    if (value == null) {
      count = DEFAULT_MAX;
    }
    else {
      count = int.parse(value, onError: (_) => DEFAULT_MAX);
    }

    this.stars = new List.generate(count, (i) => i + 1);
  }

  starClass(star) {
    if (this.rating == null || star > this.rating) {
      return STAR_OFF_CLASS;
    }
    return STAR_ON_CLASS;
  }

  starChar(star) {
    if (this.rating == null || star > this.rating) {
      return STAR_OFF_CHAR;
    }
    return STAR_ON_CHAR;
  }

  void handleClick(star) {
    this.rating = (star == 1 && this.rating == 1) ? 0 : star;
  }
}
