"use strict";

/* 
 * Kata module for notification tools
 * Can be used as a general place for various visual helper tools
 */

this.ckan.module('kata-notification-tools', function (jQuery, _) {
  return {
	  initialize: function () {
	      jQuery.proxyAll(this, /_on/);
	      this.el.on('click', this._onClick);
	  },
	  // Closes the calling element from a mouse click
	  _onClick: function () {
		  this.el.hide();
	  }
  };
});