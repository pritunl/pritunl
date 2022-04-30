define([
  'jquery',
  'underscore',
  'backbone',
  'views/modal',
  'text!templates/modalModifyLocHost.html'
], function($, _, Backbone, ModalView,
    modalModifyLocHostTemplate) {
  'use strict';
  var ModalModifyLocationView = ModalView.extend({
    className: 'modify-location-host-modal',
    template: _.template(modalModifyLocHostTemplate),
    title: 'Modify Location Host',
    okText: 'Save',
    hasAdvanced: true,
    events: function() {
      return _.extend({
        'click .static-toggle': 'onStaticSelect'
      }, ModalModifyLocationView.__super__.events);
    },
    body: function() {
      return this.template(this.model.toJSON());
    },
    getStaticSelect: function() {
      return this.$('.static-toggle .selector').hasClass('selected');
    },
    setStaticSelect: function(state) {
      if (state) {
        this.$('.static-toggle .selector').addClass('selected');
        this.$('.static-toggle .selector-inner').show();
      } else {
        this.$('.static-toggle .selector').removeClass('selected');
        this.$('.static-toggle .selector-inner').hide();
      }
    },
    onStaticSelect: function() {
      this.setStaticSelect(!this.getStaticSelect());
    },
    onOk: function() {
      var name = this.$('.name input').val();
      var timeout = parseInt(this.$('.timeout input').val(), 10) || null;
      var priority = parseInt(this.$('.priority input').val(), 10) || 1;
      var backoff = parseInt(this.$('.backoff input').val(), 10) || null;
      var staticHost = this.getStaticSelect();
      var publicAddress = this.$('.public-address input').val();
      var localAddress = this.$('.local-address input').val();
      var address6 = this.$('.address6 input').val();

      if (!name) {
        this.setAlert('danger', 'Name can not be empty.', '.name');
        return;
      }

      this.setLoading('Saving location host...');
      this.model.save({
        name: name,
        timeout: timeout,
        priority: priority,
        backoff: backoff,
        static: staticHost,
        public_address: publicAddress,
        local_address: localAddress,
        address6: address6
      }, {
        success: function() {
          this.close(true);
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
    }
  });

  return ModalModifyLocationView;
});
