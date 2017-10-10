define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalLocHostUri.html'
], function($, _, Backbone, ModalView, modalLocHostUriTemplate) {
  'use strict';
  var ModalLocHostUriView = ModalView.extend({
    className: 'location-host-uri-modal',
    template: _.template(modalLocHostUriTemplate),
    title: 'Location Host URI',
    cancelText: null,
    okText: 'Close',
    events: function() {
      return _.extend({
        'click input': 'onClickInput'
      }, ModalLocHostUriView.__super__.events);
    },
    initialize: function() {
      ModalLocHostUriView.__super__.initialize.call(this);
      this.setAlert('info', 'The hostname in the URI below may need to ' +
        'be adjusted to the hostname that the link host should use to ' +
        'access a Pritunl host. For high availability the hostname should ' +
        'be directed to a load balancer in front of several Pritunl hosts.');
    },
    body: function() {
      return this.template();
    },
    postRender: function() {
      this.setLoading('Getting location host URI...', true);
      this.model.set({
        'hostname': window.location.host
      });
      this.model.fetch({
        success: function() {
          this.clearLoading();

          var uriLink = this.model.get('uri') + window.location.host;

          this.$('.uri-link input').val(uriLink);
        }.bind(this),
        error: function(model, response) {
          this.clearLoading();
          if (response.responseJSON) {
            this.setAlert('danger', response.responseJSON.error_msg);
          }
          else {
            this.setAlert('danger', this.errorMsg);
          }
        }.bind(this)
      });
    },
    onClickInput: function(evt) {
      this.$(evt.target).select();
    }
  });

  return ModalLocHostUriView;
});
