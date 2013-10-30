// Ref: http://docs.ckan.org/en/latest/javascript-module-tutorial.html
ckan.module('delineate', function (jQuery, _) {
  return {
    initialize: function () {
      //console.log('I've been called for element: %o', this.el);
      //var script = document.createElement('script');

      //script.src='https://maps.googleapis.com/maps/api/js?key=AIzaSyA4_XHfI4dLLx2yMK2bNn0AlVEn1GvF5AU&sensor=false';
	  //script.type = 'text/javascript';
	  //document.getElementsByTagName('head')[0].appendChild(script);
     
      //this.$('#radUSICConstantOption').change(jQuery.proxy(this.showHideUSICFields));
	  //$(document).ready(jQuery.proxy(this.showMap));
	  this.$('#lat').on('input',jQuery.proxy(this.enableDelineateButton));
	  this.$('#btn_select_outlet').click(jQuery.proxy(this.disableSelectoutletButton));
	  //this.$('#btn_delineate').prop("disabled", true);
	  //this.$('#btn_showwatershed').prop("disabled", true);
	  this.$('#btn_delineate').on('submit', jQuery.proxy(this.disableDelineateButton));
	  this.$('#hidden_checkbox').hide();
	  this.$('#hidden_checkbox').change(jQuery.proxy(this.enableDelineateButton));
	  //if (this.$('#hidden_checkbox').is(":checked"))
	  //{
	  //	this.$('#btn_showwatershed').prop("disabled", false);
	  //}
	  
   },
   
    showMap: function(event) {
    	//event.preventDefault();
		var mapOptions = {
        	center: new google.maps.LatLng(38, -97), // lat long for USA
         	zoom: 3,
         	zoomControl: true,
         	mapTypeId: google.maps.MapTypeId.TERRAIN
        };
        var g_map = this.$('#gmap');
        gmap = new google.maps.Map(g_map, mapOptions);  	
    },
	
	enableDelineateButton: function(event) {
		event.preventDefault();
		this.$('#btn_delineate').prop("disabled", false);		
	},
	
	disableDelineateButton: function(event) {
		event.preventDefault();
		this.$('#btn_delineate').prop("disabled", true);		
	},
	
	disableSelectoutletButton: function(event) {
		event.preventDefault();
		this.$('#btn_select_outlet').prop("disabled", true);		
	},
  };
});