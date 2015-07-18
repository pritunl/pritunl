import 'package:angular/animate/module.dart' as anim;
import 'package:angular/core_dom/module_internal.dart' as core_dom;
import 'package:angular/core_dom/dom_util.dart' as util;
import 'package:angular/angular.dart' show Injectable;
import 'dart:html' as dom;

core_dom.Animation _animationFromList(
    Iterable<core_dom.Animation> animations) {
  if (animations == null) {
    return new core_dom.NoOpAnimation();
  }

  List<core_dom.Animation> list = animations.toList();

  if (list.length == 0) {
    return new core_dom.NoOpAnimation();
  }
  if (list.length == 1) {
    return list.first;
  }

  return new anim.AnimationList(list);
}

@Injectable()
class CustomAnimate extends anim.CssAnimate {
  static const NG_INSERT = "ng-enter";

  anim.AnimationOptimizer _optimizer;

  CustomAnimate(anim.AnimationLoop runner, anim.CssAnimationMap animationMap,
      anim.AnimationOptimizer optimizer) : super(
      runner, animationMap, optimizer) {
    this._optimizer = optimizer;
  }

  core_dom.Animation insert(Iterable<dom.Node> nodes, dom.Node parent,
      {dom.Node insertBefore}) {
    util.domInsert(nodes, parent, insertBefore: insertBefore);

    var animations = util.getElements(nodes)
      .where((el) => this._optimizer.shouldAnimate(el))
      .map((el) => animate(el, NG_INSERT));

    core_dom.Animation animation = _animationFromList(animations);

    if (animation is anim.CssAnimation) {
      dom.Element element = animation.element;

      if (element.attributes['slide-up'] == '') {
        print(element);
        var height = element.clientHeight;
        element.style.maxHeight = '0';
        element.style.overflowY = 'hidden';
        element.style.transition = 'max-height 5s ease-in-out';
        element.style.maxHeight = '${(height * 2).toString()}px';
      }
    }

    return _animationFromList(animations);
  }
}
