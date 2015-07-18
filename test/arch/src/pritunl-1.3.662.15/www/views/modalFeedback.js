define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalFeedback.html'
], function($, _, Backbone, ModalView, modalFeedbackTemplate) {
  'use strict';
  var ModalFeedbackView = ModalView.extend({
    className: 'feedback-modal',
    template: _.template(modalFeedbackTemplate),
    title: 'Anonymous Feedback/Bug Report',
    okText: 'Submit',
    enterOk: false,
    safeClose: true,
    body: function() {
      return this.template();
    },
    onOk: function() {
      var message = this.$('textarea').val();

      this.setLoading('Submitting feedback/bug report...');
      $.ajax({
          type: 'POST',
          url: 'https://app.pritunl.com/feedback',
          contentType: 'application/json',
          data: JSON.stringify({
            'message': message
          }),
          success: function() {
            this.close(true);
          }.bind(this),
          error: function() {
            this.clearLoading();
            this.setAlert('danger',
              'Failed to submit feedback, unknown server error.');
          }.bind(this)
      });
    }
  });

  return ModalFeedbackView;
});
