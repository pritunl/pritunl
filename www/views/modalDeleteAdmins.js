define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'views/alert',
  'text!templates/modalDeleteAdmins.html'
], function($, _, Backbone, ModalView, AlertView, modalDeleteAdminsTemplate) {
  'use strict';
  var ModalDeleteAdminsView = ModalView.extend({
    className: 'delete-admins-modal',
    template: _.template(modalDeleteAdminsTemplate),
    title: 'Delete Administrators',
    okText: 'Delete',
    body: function() {
      var i;
      var nameId;
      var admins = [];
      var adminsSort = [];
      var adminsObj = {};
      var data = this.collection.toJSON();

      for (i = 0; i < data.length; i++) {
        nameId = data[i].username + '_' + data[i].id;
        adminsSort.push(nameId);
        adminsObj[nameId] = data[i];
      }
      adminsSort.sort();
      for (i = 0; i < adminsSort.length; i++) {
        admins.push(adminsObj[adminsSort[i]]);
      }

      return this.template({
        admins: admins
      });
    },
    onOk: function() {
      this.setLoading('Deleting administrators...');

      var i;
      var model;
      var users = this.collection.models.slice(0);
      var error = false;
      var count = users.length;
      var destroyData = {
        success: function() {
          if (--count < 1 && !error) {
            this.close(true);
          }
        }.bind(this),
        error: function(model, response) {
          if (!error) {
            this.$('.ok').hide();
            this.$('.cancel').text('Close');
            error = true;
            this.clearLoading();
            if (response.responseJSON) {
              this.setAlert('danger', response.responseJSON.error_msg);
            }
            else {
              this.setAlert('danger', this.errorMsg);
            }
          }
        }.bind(this)
      };
      if (!count) {
        this.close();
      }
      for (i = 0; i < users.length; i++) {
        model = users[i].clone();
        model.destroy(destroyData);
      }
    }
  });

  return ModalDeleteAdminsView;
});
