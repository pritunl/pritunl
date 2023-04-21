define([
  'jquery',
  'underscore',
  'backbone',
  'views/alert',
  'views/modalDeviceRegister',
  'text!templates/devicesListItem.html'
], function($, _, Backbone, AlertView,
    ModalDeviceRegister, devicesListItemTemplate) {
  'use strict';
  var DevicesListItemView = Backbone.View.extend({
    className: 'device',
    template: _.template(devicesListItemTemplate),
    events: {
      'click .devices-device-reg': 'onRegister',
      'click .devices-device-del': 'onDelete'
    },
    initialize: function() {
    },
    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      this.update();
      return this;
    },
    update: function() {
      this.$('.link-title a').text(this.model.get('name'));

      var platform = this.model.get('platform');

      if (platform === 'win') {
        platform = 'windows';
      }
      else if (platform === 'mac' || platform === 'ios') {
        platform = 'apple';
      }
      else if (platform === 'linux' || platform === 'chrome' ||
          platform === 'android') {
        platform = platform;
      }
      else {
        platform = 'desktop';
      }

      if (platform) {
        this.$('.devices-device .name-icon').removeClass(
          'glyphicon glyphicon-tasks fa fa-windows fa-apple ' +
          'fa-linux fa-desktop');
        this.$('.devices-device .name-icon').addClass('fa fa-' + platform);
      }

      if (this.model.get('status') === 'online') {
        this.$('.link-start').hide();
        this.$('.link-stop').show();
      } else {
        this.$('.link-stop').hide();
        this.$('.link-start').show();
      }
    },
    onRegister: function() {
      var model = this.model.clone();

      var modal = new ModalDeviceRegister({
        model: model
      });
      this.listenToOnce(modal, 'applied', function() {
        var alertView = new AlertView({
          type: 'success',
          message: 'Successfully registered device.',
          dismissable: true
        });
        $('.alerts-container').append(alertView.render().el);
      }.bind(this));
      this.addView(modal);
    },
    onDelete: function() {
      var model = this.model.clone();

      model.destroy();
      //this.devicesView.destroy();
    }
  });

  return DevicesListItemView;
});
