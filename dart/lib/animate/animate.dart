library animate;

import 'package:pritunl/animate/custom.dart' as custom;

import 'package:angular/animate/module.dart' as anim;
import 'package:angular/core_dom/module_internal.dart' as core_dom;
import 'package:angular/angular.dart' as ng;

class AnimationModule extends ng.Module {
  AnimationModule() {
    bind(anim.AnimationFrame);
    bind(anim.AnimationLoop);
    bind(anim.CssAnimationMap);
    bind(anim.AnimationOptimizer);
    bind(anim.NgAnimate, toValue: null);
    bind(anim.NgAnimateChildren);
    bind(core_dom.Animate, toImplementation: custom.CustomAnimate);
  }
}
