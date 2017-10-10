define([
  'jquery',
  'underscore',
  'backbone',
  'models/userBulk',
  'views/modal',
  'views/alert',
  'text!templates/modalAddUserBulk.html'
], function($, _, Backbone, UserBulkModel, ModalView, AlertView,
    modalAddUserBulkTemplate) {
  'use strict';
  var lastOrg;
  var ModalAddUserBulkView = ModalView.extend({
    className: 'add-user-bulk-modal',
    template: _.template(modalAddUserBulkTemplate),
    title: 'Bulk Add Users',
    okText: 'Add',
    enterOk: false,
    safeClose: true,
    initialize: function(options) {
      this.orgs = options.orgs;
      ModalAddUserBulkView.__super__.initialize.call(this);
    },
    body: function() {
      return this.template({
        orgs: this.orgs.toJSON(),
        lastOrg: lastOrg
      });
    },
    onOk: function() {
      var i;
      var userLine;
      var userLines = this.$('.users textarea').val().split('\n');
      var org = this.$('.org select').val();
      var model = new UserBulkModel();
      var emailReg = /^\w+([-+.']\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/;

      for (i = 0; i < userLines.length; i++) {
        userLine = userLines[i].split(',');
        if (!userLine[0]) {
          continue;
        }
        if (userLine[1] && !emailReg.test(userLine[1])) {
          this.setAlert('danger', 'Email "' + userLine[1] + '" not valid.',
            '.form-group.users');
          return;
        }
        model.addUser(userLine[0], userLine[1]);
      }
      lastOrg = org;

      this.$('.users textarea').attr('disabled', 'disabled');
      this.$('.org select').attr('disabled', 'disabled');
      this.setLoading('Adding users...');
      model.save({
        organization: org
      }, {
        success: function(_, response) {
          if (response.status === 'users_background') {
            this.close(true, response.status_msg);
          } else {
            this.close(true);
          }
        }.bind(this),
        error: function(model, response) {
          this.$('.users textarea').removeAttr('disabled');
          this.$('.org select').removeAttr('disabled');
          this.clearLoading();
          if (response.responseJSON) {
            this.setAlert('danger', response.responseJSON.error_msg);
          }
          else {
            this.setAlert('danger', this.errorMsg);
          }
        }.bind(this)
      });
    }
  });

  return ModalAddUserBulkView;
});
