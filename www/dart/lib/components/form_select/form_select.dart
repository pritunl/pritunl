library form_select_comp;

import 'package:pritunl/bases/form_control/form_control.dart' as
  form_control_base;

import 'package:angular/angular.dart' show Component, NgCallback, NgTwoWay,
  NgOneWay, NgAttr;

@Component(
  selector: 'x-form-select',
  template: '<select ng-model="model" tooltip="{{formTooltip}}">'
    '<option ng-repeat="colModel in collection" '
    'ng-value="optValue({\'\$model\': colModel})">'
    '{{optText({\'\$model\': colModel})}}</option></select>',
  cssUrl: 'packages/pritunl/components/form_select/form_select.css'
)
class FormSelectComp extends form_control_base.FormControlBase {
  String controlSelector = 'select';

  @NgAttr('form-tooltip')
  String formTooltip;

  @NgAttr('type')
  String type;

  @NgAttr('placeholder')
  String placeholder;

  var _model;
  @NgTwoWay('model')
  String get model {
    if (this._model == null) {
      if (this.collection != null) {
        for (var model in this.collection) {
          this._model = this.optValue({r'$model': model});
          break;
        }
      }
    }
    return this._model;
  }
  void set model(String val) {
    this._model = val;
  }

  @NgOneWay('collection')
  Iterable collection;

  @NgCallback('opt-value')
  Function optValue;

  @NgCallback('opt-text')
  Function optText;
}
