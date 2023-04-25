define([
  'jquery',
  'underscore',
  'backbone',
  'views/alert',
  'views/modalDeviceRegister',
  'views/modalDeleteUserDevice',
  'text!templates/userDevicesListItem.html'
], function($, _, Backbone, AlertView, ModalDeviceRegister,
    ModalDeleteUserDevice, userServersListItemTemplate) {
  'use strict';
  var UserServersListItemView = Backbone.View.extend({
    className: 'user-device',
    template: _.template(userServersListItemTemplate),
    events: {
      'click .user-device-reg': 'onRegister',
      'click .user-device-del': 'onDelete',
    },
    render: function() {
      this.$el.html(this.template());
      this.update();
      this.$('.server-item').tooltip();
      return this;
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
    onDelete: function(evt) {
      var model = this.model.clone();

      if (evt.shiftKey && evt.ctrlKey && evt.altKey) {
        model.destroy();
        return;
      }

      var modal = new ModalDeleteUserDevice({
        model: model
      });
      this.addView(modal);
    },
    update: function() {
      this.$('.device-name .title').text(this.model.get('name'));

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
        this.$('.name-icon').removeClass(
          'glyphicon glyphicon-tasks fa fa-windows fa-apple ' +
          'fa-linux fa-desktop');
        this.$('.name-icon').addClass('fa fa-' + platform);
      }

      if (this.model.get('timestamp')) {
        this.$('.device-time .title').text(
          window.formatTime(this.model.get('timestamp')));
        this.$('.device-time').show();
      }
      else {
        this.$('.server-time').hide();
      }

      if (this.model.get('registered')) {
        this.$('.user-device-unregisted-label').hide();
        this.$('.user-device-reg').hide();
      } else {
        this.$('.user-device-unregisted-label').css(
          'display', 'inline-block');
        this.$('.user-device-reg').show();
      }
    }
  });

  return UserServersListItemView;
});
