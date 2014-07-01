// Ref: http://docs.ckan.org/en/latest/javascript-module-tutorial.html
ckan.module('package_create', function (jQuery, _) {
  return {
    initialize: function () {
      //console.log('I've been called for element: %o', this.el);

      this.$('#field-pkgname').focus();

      // track the radio button checked status change event
      this.$('#radDomainPolygonFileType').change(jQuery.proxy(this.showHidePolygonFileSelection));
      this.$('#radDomainNetCDFFileType').change(jQuery.proxy(this.showHideNetCDFFileSelection));
      this.$('#radParametersFileOptionYes').change(jQuery.proxy(this.showHideParameterFileSelection));
      this.$('#radParametersFileOptionNo').change(jQuery.proxy(this.showHideParameterFileSelection));
      
      this.$('#radUSICConstantOption').change(jQuery.proxy(this.showHideUSICFields));
      this.$('#radUSICGridOption').change(jQuery.proxy(this.showHideUSICFields));
      
      this.$('#radWSISConstantOption').change(jQuery.proxy(this.showHideWSISFields));
      this.$('#radWSISGridOption').change(jQuery.proxy(this.showHideWSISFields));
      
      this.$('#radTICConstantOption').change(jQuery.proxy(this.showHideTICFields));
      this.$('#radTICGridOption').change(jQuery.proxy(this.showHideTICFields));
      
      this.$('#radWCICConstantOption').change(jQuery.proxy(this.showHideWCICFields));
      this.$('#radWCICGridOption').change(jQuery.proxy(this.showHideWCICFields));
      
      this.$('#radDFConstantOption').change(jQuery.proxy(this.showHideDFFields));
      this.$('#radDFGridOption').change(jQuery.proxy(this.showHideDFFields));
      
      this.$('#radAepConstantOption').change(jQuery.proxy(this.showHideAEPFields));
      this.$('#radAepGridOption').change(jQuery.proxy(this.showHideAEPFields));
      
      this.$('#radSbarConstantOption').change(jQuery.proxy(this.showHideSBARFields));
      this.$('#radSbarGridOption').change(jQuery.proxy(this.showHideSBARFields));
      
      this.$('#radSubalbConstantOption').change(jQuery.proxy(this.showHideSUBALBFields));
      this.$('#radSubalbGridOption').change(jQuery.proxy(this.showHideSUBALBFields));
      
      this.$('#radSubtypeConstantOption').change(jQuery.proxy(this.showHideSUBTYPEFields));
      this.$('#radSubtypeGridOption').change(jQuery.proxy(this.showHideSUBTYPEFields));
      
      this.$('#radGsurfConstantOption').change(jQuery.proxy(this.showHideGSURFFields));
      this.$('#radGsurfGridOption').change(jQuery.proxy(this.showHideGSURFFields));
      
      this.$('#radTslastConstantOption').change(jQuery.proxy(this.showHideTSLASTFields));
      this.$('#radTslastGridOption').change(jQuery.proxy(this.showHideTSLASTFields));
      
      this.$('#radCCNLCDOption').change(jQuery.proxy(this.showHideCCFields));
      this.$('#radCCConstantOption').change(jQuery.proxy(this.showHideCCFields));
      this.$('#radCCGridOption').change(jQuery.proxy(this.showHideCCFields));
      
      this.$('#radHcanNLCDOption').change(jQuery.proxy(this.showHideHCANFields));
      this.$('#radHcanConstantOption').change(jQuery.proxy(this.showHideHCANFields));
      this.$('#radHcanGridOption').change(jQuery.proxy(this.showHideHCANFields));
      
      this.$('#radLaiNLCDOption').change(jQuery.proxy(this.showHideLAIFields));
      this.$('#radLaiConstantOption').change(jQuery.proxy(this.showHideLAIFields));
      this.$('#radLaiGridOption').change(jQuery.proxy(this.showHideLAIFields));
      
      this.$('#radYcageNLCDOption').change(jQuery.proxy(this.showHideYCAGEFields));
      this.$('#radYcageConstantOption').change(jQuery.proxy(this.showHideYCAGEFields));
      this.$('#radYcageGridOption').change(jQuery.proxy(this.showHideYCAGEFields));
      
      this.$('#radAprComputeOption').change(jQuery.proxy(this.showHideAprFields));
      this.$('#radAprConstantOption').change(jQuery.proxy(this.showHideAprFields));
      this.$('#radAprGridOption').change(jQuery.proxy(this.showHideAprFields));
      
      this.$('#radSlopeComputeOption').change(jQuery.proxy(this.showHideSlopeFields));
      this.$('#radSlopeConstantOption').change(jQuery.proxy(this.showHideSlopeFields));
      this.$('#radSlopeGridOption').change(jQuery.proxy(this.showHideSlopeFields));
      
      this.$('#radAspectComputeOption').change(jQuery.proxy(this.showHideAspectFields));
      this.$('#radAspectConstantOption').change(jQuery.proxy(this.showHideAspectFields));
      this.$('#radAspectGridOption').change(jQuery.proxy(this.showHideAspectFields));
      
      this.$('#radLatComputeOption').change(jQuery.proxy(this.showHideLatitudeFields));
      this.$('#radLatConstantOption').change(jQuery.proxy(this.showHideLatitudeFields));
      this.$('#radLatGridOption').change(jQuery.proxy(this.showHideLatitudeFields));
      
      this.$('#radLonComputeOption').change(jQuery.proxy(this.showHideLongitudeFields));
      this.$('#radLonConstantOption').change(jQuery.proxy(this.showHideLongitudeFields));
      this.$('#radLonGridOption').change(jQuery.proxy(this.showHideLongitudeFields));
      
      this.$('#radTempComputeOption').change(jQuery.proxy(this.showHideTemperatureFields));
      this.$('#radTempConstantOption').change(jQuery.proxy(this.showHideTemperatureFields));
      this.$('#radTempTextOption').change(jQuery.proxy(this.showHideTemperatureFields));
      this.$('#radTempGridOption').change(jQuery.proxy(this.showHideTemperatureFields));
      
      this.$('#radPrecComputeOption').change(jQuery.proxy(this.showHidePrecipitationFields));
      this.$('#radPrecConstantOption').change(jQuery.proxy(this.showHidePrecipitationFields));
      this.$('#radPrecTextOption').change(jQuery.proxy(this.showHidePrecipitationFields));
      this.$('#radPrecGridOption').change(jQuery.proxy(this.showHidePrecipitationFields));
      
      this.$('#radWindComputeOption').change(jQuery.proxy(this.showHideWindFields));
      this.$('#radWindConstantOption').change(jQuery.proxy(this.showHideWindFields));
      this.$('#radWindTextOption').change(jQuery.proxy(this.showHideWindFields));
      this.$('#radWindGridOption').change(jQuery.proxy(this.showHideWindFields));
      
      this.$('#radRhComputeOption').change(jQuery.proxy(this.showHideRhFields));
      this.$('#radRhConstantOption').change(jQuery.proxy(this.showHideRhFields));
      this.$('#radRhTextOption').change(jQuery.proxy(this.showHideRhFields));
      this.$('#radRhGridOption').change(jQuery.proxy(this.showHideRhFields));
      
      this.$('#radSnowalbComputeOption').change(jQuery.proxy(this.showHideSnowalbFields));
      this.$('#radSnowalbConstantOption').change(jQuery.proxy(this.showHideSnowalbFields));
      this.$('#radSnowalbTextOption').change(jQuery.proxy(this.showHideSnowalbFields));
      this.$('#radSnowalbGridOption').change(jQuery.proxy(this.showHideSnowalbFields));
      
      this.$('#radQgConstantOption').change(jQuery.proxy(this.showHideQgFields));
      this.$('#radQgTextOption').change(jQuery.proxy(this.showHideQgFields));
      this.$('#radQgGridOption').change(jQuery.proxy(this.showHideQgFields));
      
      this.$('#radDefaultOutputControlFileYes').change(jQuery.proxy(this.showHideOutputControlFileFields));
      this.$('#radDefaultOutputControlFileNo').change(jQuery.proxy(this.showHideOutputControlFileFields));
      
      this.$('#radDefaultAggrOutputControlFileYes').change(jQuery.proxy(this.showHideAggrOutputControlFileFields));
      this.$('#radDefaultAggrOutputControlFileNo').change(jQuery.proxy(this.showHideAggrOutputControlFileFields));
      
      // initially show the shape file selection field and hide the netcdf file selection field
      if (this.$('#radDomainPolygonFileType').is(':checked')){
  		this.$('#domainShapeFileSelection').show();
  		this.$('#domainNetCDFFileSelection').hide();
	  }
	  else
	  {
	  	this.$('#domainShapeFileSelection').hide();
	  	this.$('#domainNetCDFFileSelection').show();
	  }	  	
      
	  if (this.$('#radParametersFileOptionYes').is(':checked')){
  		this.$('#parametersFileSelection').hide();
  	  }
  	  else {
  	  	this.$('#parametersFileSelection').show();
  	  }
  	  
  	  if (this.$('#radUSICConstantOption').is(':checked')){
  		this.$('#usic_constant').show();
  		this.$('#usic_gridfile').hide();  		
  	  }
  	  else {
  	  	this.$('#usic_constant').hide();
  		this.$('#usic_gridfile').show();  		
  	  }
  	  
  	  if (this.$('#radWSISConstantOption').is(':checked')){
  		this.$('#wsis_constant').show();
  		this.$('#wsis_gridfile').hide();  		
  	  }
  	  else {
  	  	this.$('#wsis_constant').hide();
  		this.$('#wsis_gridfile').show();  		
  	  }
  	  
  	  if (this.$('#radTICConstantOption').is(':checked')){
  		this.$('#tic_constant').show();
  		this.$('#tic_gridfile').hide();  		
  	  }
  	  else {
  	  	this.$('#tic_constant').hide();
  		this.$('#tic_gridfile').show();  		
  	  }
  	  
  	  if (this.$('#radWCICConstantOption').is(':checked')){
  		this.$('#wcic_constant').show();
  		this.$('#wcic_gridfile').hide();  		
  	  }
  	  else {
  	  	this.$('#wcic_constant').hide();
  		this.$('#wcis_gridfile').show();  		
  	  }
  	  
  	  if (this.$('#radDFConstantOption').is(':checked')){
		this.$('#df_constant').show();
		this.$('#df_gridfile').hide();			
	  }
	  else {
		this.$('#df_constant').hide();
		this.$('#df_gridfile').show();						
	  }
		
  	  if (this.$('#radAepConstantOption').is(':checked')){
  		this.$('#aep_constant').show();
  		this.$('#aep_gridfile').hide();  		
  	  }
  	  else {
  	  	this.$('#aep_constant').hide();
  		this.$('#aep_gridfile').show();  		
  	  }
  	  
  	  if (this.$('#radSbarConstantOption').is(':checked')){
  		this.$('#sbar_constant').show();
  		this.$('#sbar_gridfile').hide();  		
  	  }
  	  else {
  	  	this.$('#sbar_constant').hide();
  		this.$('#sbar_gridfile').show();  		
  	  }
  	  
  	  if (this.$('#radSubalbConstantOption').is(':checked')){
  		this.$('#subalb_constant').show();
  		this.$('#subalb_gridfile').hide();  		
  	  }
  	  else {
  	  	this.$('#subalb_constant').hide();
  		this.$('#subalb_gridfile').show();  		
  	  }
  	  
  	  if (this.$('#radSubtypeConstantOption').is(':checked')){
  		this.$('#subtype_constant').show();
  		this.$('#subtype_gridfile').hide();  		
  	  }
  	  else {
  	  	this.$('#subtype_constant').hide();
  		this.$('#subtype_gridfile').show();  		
  	  }
  	  
  	  if (this.$('#radGsurfConstantOption').is(':checked')){
  		this.$('#gsurf_constant').show();
  		this.$('#gsurf_gridfile').hide();  		
  	  }
  	  else {
  	  	this.$('#gsurf_constant').hide();
  		this.$('#gsurf_gridfile').show();  		
  	  }
  	  
  	  if (this.$('#radTslastConstantOption').is(':checked')){
  		this.$('#tslast_constant').show();
  		this.$('#tslast_gridfile').hide();  		
  	  }
  	  else {
  	  	this.$('#tslast_constant').hide();
  		this.$('#tslast_gridfile').show();  		
  	  }
  	  
  	  if (this.$('#radCCConstantOption').is(':checked')){
  		this.$('#cc_constant').show();
  		this.$('#cc_gridfile').hide();  		
  	  }
  	  else if (this.$('#radCCGridOption').is(':checked')){
  	  	this.$('#cc_constant').hide();
  		this.$('#cc_gridfile').show();  		
  	  }
  	  else{
  	  	this.$('#cc_constant').hide();
  		this.$('#cc_gridfile').hide();  
  	  }
  	  
  	  if (this.$('#radHcanConstantOption').is(':checked')){
	  	this.$('#hcan_constant').show();
	  	this.$('#hcan_gridfile').hide();  		
	  }
	  else if (this.$('#radHcanGridOption').is(':checked')){
	  	this.$('#hcan_constant').hide();
	  	this.$('#hcan_gridfile').show();  		
	  }
	  else{
	  	this.$('#hcan_constant').hide();
	  	this.$('#hcan_gridfile').hide();  
	  }
	  
	  if (this.$('#radLaiConstantOption').is(':checked')){
	  	this.$('#lai_constant').show();
	  	this.$('#lai_gridfile').hide();  		
	  }
	  else if (this.$('#radLaiGridOption').is(':checked')){
	  	this.$('#lai_constant').hide();
	  	this.$('#lai_gridfile').show();  		
	  }
	  else{
	  	this.$('#lai_constant').hide();
	  	this.$('#lai_gridfile').hide();  
	  }
	  
	  if (this.$('#radYcageConstantOption').is(':checked')){
	  		this.$('#ycage_constant').show();
	  		this.$('#ycage_gridfile').hide();  		
	  }
	  else if (this.$('#radYcageGridOption').is(':checked')){
	  	  	this.$('#ycage_constant').hide();
	  		this.$('#ycage_gridfile').show();  		
	  }
	  else{
	  	  	this.$('#ycage_constant').hide();
	  		this.$('#ycage_gridfile').hide();  
	  }
	  	
	  if (this.$('#radAprConstantOption').is(':checked')){
	  	this.$('#apr_constant').show();
	  	this.$('#apr_gridfile').hide();  		
	  }
	  else if (this.$('#radAprGridOption').is(':checked')){
	  	this.$('#apr_constant').hide();
	  	this.$('#apr_gridfile').show();  		
	  }
	  else{ //
	  	this.$('#apr_constant').hide();
	  	this.$('#apr_gridfile').hide();  
	  }
	  
	  if (this.$('#radSlopeConstantOption').is(':checked')){
	  	this.$('#slope_constant').show();
	  	this.$('#slope_gridfile').hide();  		
	  }
	  else if (this.$('#radSlopeGridOption').is(':checked')){
	  	this.$('#slope_constant').hide();
	  	this.$('#slope_gridfile').show();  		
	  }
	  else{ //
	  	this.$('#slope_constant').hide();
	  	this.$('#slope_gridfile').hide();  
	  }
	  
	  if (this.$('#radAspectConstantOption').is(':checked')){
	  	this.$('#aspect_constant').show();
	  	this.$('#aspect_gridfile').hide();  		
	  }
	  else if (this.$('#radAspectGridOption').is(':checked')){
	  	this.$('#aspect_constant').hide();
	  	this.$('#aspect_gridfile').show();  		
	  }
	  else{ //
	  	this.$('#aspect_constant').hide();
	  	this.$('#aspect_gridfile').hide();  
	  }
	  
	  if (this.$('#radLatConstantOption').is(':checked')){
	  	this.$('#lat_constant').show();
	  	this.$('#lat_gridfile').hide();  		
	  }
	  else if (this.$('#radLatGridOption').is(':checked')){
	  	this.$('#lat_constant').hide();
	  	this.$('#lat_gridfile').show();  		
	  }
	  else{ //
	  	this.$('#lat_constant').hide();
	  	this.$('#lat_gridfile').hide();  
	  }
	  
	  if (this.$('#radLonConstantOption').is(':checked')){
	  	this.$('#lon_constant').show();
	  	this.$('#lon_gridfile').hide();  		
	  }
	  else if (this.$('#radLonGridOption').is(':checked')){
	  	this.$('#lon_constant').hide();
	  	this.$('#lon_gridfile').show();  		
	  }
	  else{ //
	  	this.$('#lon_constant').hide();
	  	this.$('#lon_gridfile').hide();  
	  }
	  
	  if (this.$('#radTempConstantOption').is(':checked')){
	  	this.$('#temp_constant').show();
	  	this.$('#temp_textfile').hide();
	  	this.$('#temp_gridfile').hide();  		
	  }
	  else if (this.$('#radTempTextOption').is(':checked')){
	  	this.$('#temp_textfile').show();
	  	this.$('#temp_constant').hide();
	  	this.$('#temp_gridfile').hide();  		
	  }
	  else if (this.$('#radTempGridOption').is(':checked')){
	  	this.$('#temp_textfile').hide();
	  	this.$('#temp_constant').hide();
	  	this.$('#temp_gridfile').show();  
	  }
	  else{ //
	  	this.$('#temp_constant').hide();
	  	this.$('#temp_textfile').hide();
	  	this.$('#temp_gridfile').hide();  
	  }
	  
	  if (this.$('#radPrecConstantOption').is(':checked')){
	  	this.$('#prec_constant').show();
	  	this.$('#prec_textfile').hide();
	  	this.$('#prec_gridfile').hide();  		
	  }
	  else if (this.$('#radPrecTextOption').is(':checked')){
	  	this.$('#prec_textfile').show();
	  	this.$('#prec_constant').hide();
	  	this.$('#prec_gridfile').hide();  		
	  }
	  else if (this.$('#radPrecGridOption').is(':checked')){
	  	this.$('#prec_textfile').hide();
	  	this.$('#prec_constant').hide();
	  	this.$('#prec_gridfile').show();  
	  }
	  else{ //
	  	this.$('#prec_constant').hide();
	  	this.$('#prec_textfile').hide();
	  	this.$('#prec_gridfile').hide();  
	  }
	  
	  if (this.$('#radWindConstantOption').is(':checked')){
	  	this.$('#wind_constant').show();
	  	this.$('#wind_textfile').hide();
	  	this.$('#wind_gridfile').hide();  		
	  }
	  else if (this.$('#radWindTextOption').is(':checked')){
	  	this.$('#wind_textfile').show();
	  	this.$('#wind_constant').hide();
	  	this.$('#wind_gridfile').hide();  		
	  }
	  else if (this.$('#radWindGridOption').is(':checked')){
	  	this.$('#wind_textfile').hide();
	  	this.$('#wind_constant').hide();
	  	this.$('#wind_gridfile').show();  
	  }
	  else{ //
	  	this.$('#wind_constant').hide();
	  	this.$('#wind_textfile').hide();
	  	this.$('#wind_gridfile').hide();  
	  }
	  
	  if (this.$('#radRhConstantOption').is(':checked')){
	  	this.$('#rh_constant').show();
	  	this.$('#rh_textfile').hide();
	  	this.$('#rh_gridfile').hide();  		
	  }
	  else if (this.$('#radRhTextOption').is(':checked')){
	  	this.$('#rh_textfile').show();
	  	this.$('#rh_constant').hide();
	  	this.$('#rh_gridfile').hide();  		
	  }
	  else if (this.$('#radRhGridOption').is(':checked')){
	  	this.$('#rh_textfile').hide();
	  	this.$('#rh_constant').hide();
	  	this.$('#rh_gridfile').show();  
	  }
	  else{ //
	  	this.$('#rh_constant').hide();
	  	this.$('#rh_textfile').hide();
	  	this.$('#rh_gridfile').hide();  
	  }
	  
	  if (this.$('#radSnowalbConstantOption').is(':checked')){
	  	this.$('#snowalb_constant').show();
	  	this.$('#snowalb_textfile').hide();
	  	this.$('#snowalb_gridfile').hide();  		
	  }
	  else if (this.$('#radSnowalbTextOption').is(':checked')){
	  	this.$('#snowalb_textfile').show();
	  	this.$('#snowalb_constant').hide();
	  	this.$('#snowalb_gridfile').hide();  		
	  }
	  else if (this.$('#radSnowalbGridOption').is(':checked')){
	  	this.$('#snowalb_textfile').hide();
	  	this.$('#snowalb_constant').hide();
	  	this.$('#snowalb_gridfile').show();  
	  }
	  else{ //
	  	this.$('#snowalb_constant').hide();
	  	this.$('#snowalb_textfile').hide();
	  	this.$('#snowalb_gridfile').hide();  
	  }
	  
	  if (this.$('#radQgConstantOption').is(':checked')){
	  	this.$('#qg_constant').show();
	  	this.$('#qg_textfile').hide();
	  	this.$('#qg_gridfile').hide();  		
	  }
	  else if (this.$('#radQgTextOption').is(':checked')){
	  	this.$('#qg_textfile').show();
	  	this.$('#qg_constant').hide();
	  	this.$('#qg_gridfile').hide();  		
	  }
	  else if (this.$('#radQgGridOption').is(':checked')){
	  	this.$('#qg_textfile').hide();
	  	this.$('#qg_constant').hide();
	  	this.$('#qg_gridfile').show();  
	  }
	  
	  if (this.$('#radDefaultOutputControlFileYes').is(':checked')){  		
  		this.$('#output_controlfile').hide();
	  }
	  else {
	  	this.$('#output_controlfile').show();	  	
	  }	
	  
	  if (this.$('#radDefaultAggrOutputControlFileYes').is(':checked')){  		
  		this.$('#aggroutput_controlfile').hide();
	  }
	  else {
	  	this.$('#aggroutput_controlfile').show();	  	
	  }	
    },

    showHidePolygonFileSelection: function(event) {
    	event.preventDefault();
		if ($('#radDomainPolygonFileType').is(':checked')){
	  		$('#domainShapeFileSelection').show();
	  		$('#domainNetCDFFileSelection').hide();
	  	}	  	
    },
    
    showHideNetCDFFileSelection: function(event) {
    	event.preventDefault();
		if ($('#radDomainNetCDFFileType').is(':checked')){
	  		$('#domainShapeFileSelection').hide();
	  		$('#domainNetCDFFileSelection').show();
	  	}	  	
    },
    
    showHideParameterFileSelection: function(event) {
    	event.preventDefault();
		if ($('#radParametersFileOptionYes').is(':checked')){
			$('#parametersFileSelection').hide();
		}
		if ($('#radParametersFileOptionNo').is(':checked')){
			$('#parametersFileSelection').show();
		}
	},
	
	showHideUSICFields: function(event) {
    	event.preventDefault();
		if ($('#radUSICConstantOption').is(':checked')){
			$('#usic_constant').show();
			$('#usic_gridfile').hide();			
		}
		if ($('#radUSICGridOption').is(':checked')){
			$('#usic_constant').hide();
			$('#usic_gridfile').show();					
		}
	},
	
	showHideWSISFields: function(event) {
    	event.preventDefault();
		if ($('#radWSISConstantOption').is(':checked')){
			$('#wsis_constant').show();
			$('#wsis_gridfile').hide();			
		}
		if ($('#radWSISGridOption').is(':checked')){
			$('#wsis_constant').hide();
			$('#wsis_gridfile').show();						
		}
	},
	
	showHideTICFields: function(event) {
    	event.preventDefault();
		if ($('#radTICConstantOption').is(':checked')){
			$('#tic_constant').show();
			$('#tic_gridfile').hide();			
		}
		if ($('#radTICGridOption').is(':checked')){
			$('#tic_constant').hide();
			$('#tic_gridfile').show();						
		}
	},
	
	showHideWCICFields: function(event) {
    	event.preventDefault();
		if ($('#radWCICConstantOption').is(':checked')){
			$('#wcic_constant').show();
			$('#wcic_gridfile').hide();			
		}
		if ($('#radWCICGridOption').is(':checked')){
			$('#wcic_constant').hide();
			$('#wcic_gridfile').show();						
		}
	},
	
	showHideDFFields: function(event) {
    	event.preventDefault();
		if ($('#radDFConstantOption').is(':checked')){
			$('#df_constant').show();
			$('#df_gridfile').hide();			
		}
		if ($('#radDFGridOption').is(':checked')){
			$('#df_constant').hide();
			$('#df_gridfile').show();						
		}
	},
	
	showHideAEPFields: function(event) {
    	event.preventDefault();
		if ($('#radAepConstantOption').is(':checked')){
			$('#aep_constant').show();
			$('#aep_gridfile').hide();			
		}
		if ($('#radAepGridOption').is(':checked')){
			$('#aep_constant').hide();
			$('#aep_gridfile').show();						
		}
	},
	
	showHideSBARFields: function(event) {
    	event.preventDefault();
		if ($('#radSbarConstantOption').is(':checked')){
			$('#sbar_constant').show();
			$('#sbar_gridfile').hide();			
		}
		if ($('#radSbarGridOption').is(':checked')){
			$('#sbar_constant').hide();
			$('#sbar_gridfile').show();						
		}
	},
	
	showHideSUBALBFields: function(event) {
    	event.preventDefault();
		if ($('#radSubalbConstantOption').is(':checked')){
			$('#subalb_constant').show();
			$('#subalb_gridfile').hide();			
		}
		if ($('#radSubalbGridOption').is(':checked')){
			$('#subalb_constant').hide();
			$('#subalb_gridfile').show();						
		}
	},
	
	showHideSUBTYPEFields: function(event) {
    	event.preventDefault();
		if ($('#radSubtypeConstantOption').is(':checked')){
			$('#subtype_constant').show();
			$('#subtype_gridfile').hide();			
		}
		if ($('#radSubtypeGridOption').is(':checked')){
			$('#subtype_constant').hide();
			$('#subtype_gridfile').show();						
		}
	},
	
	showHideGSURFFields: function(event) {
    	event.preventDefault();
		if ($('#radGsurfConstantOption').is(':checked')){
			$('#gsurf_constant').show();
			$('#gsurf_gridfile').hide();			
		}
		if ($('#radGsurfGridOption').is(':checked')){
			$('#gsurf_constant').hide();
			$('#gsurf_gridfile').show();						
		}
	},
	
	showHideTSLASTFields: function(event) {
    	event.preventDefault();
		if ($('#radTslastConstantOption').is(':checked')){
			$('#tslast_constant').show();
			$('#tslast_gridfile').hide();			
		}
		if ($('#radTslastGridOption').is(':checked')){
			$('#tslast_constant').hide();
			$('#tslast_gridfile').show();						
		}
	},
	
	showHideCCFields: function(event) {
    	event.preventDefault();
    	if ($('#radCCConstantOption').is(':checked')){
	  		$('#cc_constant').show();
	  		$('#cc_gridfile').hide();  		
	  	}
	  	else if ($('#radCCGridOption').is(':checked')){
	  	  	$('#cc_constant').hide();
	  		$('#cc_gridfile').show();  		
	  	}
	  	else{
	  	  	$('#cc_constant').hide();
	  		$('#cc_gridfile').hide();  
	  	}
	},
	
	showHideHCANFields: function(event) {
    	event.preventDefault();
    	if ($('#radHcanConstantOption').is(':checked')){
	  		$('#hcan_constant').show();
	  		$('#hcan_gridfile').hide();  		
	  	}
	  	else if ($('#radHcanGridOption').is(':checked')){
	  	  	$('#hcan_constant').hide();
	  		$('#hcan_gridfile').show();  		
	  	}
	  	else{
	  	  	$('#hcan_constant').hide();
	  		$('#hcan_gridfile').hide();  
	  	}
	},
	
	showHideLAIFields: function(event) {
    	event.preventDefault();
    	if ($('#radLaiConstantOption').is(':checked')){
	  		$('#lai_constant').show();
	  		$('#lai_gridfile').hide();  		
	  	}
	  	else if ($('#radLaiGridOption').is(':checked')){
	  	  	$('#lai_constant').hide();
	  		$('#lai_gridfile').show();  		
	  	}
	  	else{
	  	  	$('#lai_constant').hide();
	  		$('#lai_gridfile').hide();  
	  	}
	},
	
	showHideYCAGEFields: function(event) {
    	event.preventDefault();
    	if ($('#radYcageConstantOption').is(':checked')){
	  		$('#ycage_constant').show();
	  		$('#ycage_gridfile').hide();  		
	  	}
	  	else if ($('#radYcageGridOption').is(':checked')){
	  	  	$('#ycage_constant').hide();
	  		$('#ycage_gridfile').show();  		
	  	}
	  	else{
	  	  	$('#ycage_constant').hide();
	  		$('#ycage_gridfile').hide();  
	  	}
	},
	
	showHideAprFields: function(event) {
    	event.preventDefault();
    	if ($('#radAprConstantOption').is(':checked')){
	  		$('#apr_constant').show();
	  		$('#apr_gridfile').hide();  		
	  	}
	  	else if ($('#radAprGridOption').is(':checked')){
	  	  	$('#apr_constant').hide();
	  		$('#apr_gridfile').show();  		
	  	}
	  	else{ //apr compute option selected
	  	  	$('#apr_constant').hide();
	  		$('#apr_gridfile').hide();  
	  	}
	},
	
	showHideSlopeFields: function(event) {
    	event.preventDefault();
    	if ($('#radSlopeConstantOption').is(':checked')){
		  	$('#slope_constant').show();
		  	$('#slope_gridfile').hide();  		
		}
		else if ($('#radSlopeGridOption').is(':checked')){
		  	$('#slope_constant').hide();
		  	$('#slope_gridfile').show();  		
		}
		else{ // compute option selected
		  	$('#slope_constant').hide();
		  	$('#slope_gridfile').hide();  
		}
	},
	
	showHideAspectFields: function(event) {
    	event.preventDefault();
    	if ($('#radAspectConstantOption').is(':checked')){
	  		$('#aspect_constant').show();
	  		$('#aspect_gridfile').hide();  		
	  	}
	  	else if ($('#radAspectGridOption').is(':checked')){
	  		$('#aspect_constant').hide();
	  		$('#aspect_gridfile').show();  		
	  	}
	  	else{ // compute option selected
	  		$('#aspect_constant').hide();
	  		$('#aspect_gridfile').hide();  
	  	}
   },
   
   showHideLatitudeFields: function(event) {
    	event.preventDefault();
    	if ($('#radLatConstantOption').is(':checked')){
	  		$('#lat_constant').show();
	  		$('#lat_gridfile').hide();  		
	  	}
	  	else if ($('#radLatGridOption').is(':checked')){
	  		$('#lat_constant').hide();
	  		$('#lat_gridfile').show();  		
	  	}
	  	else{ // compute option selected
	  		$('#lat_constant').hide();
	  		$('#lat_gridfile').hide();  
	  }
   },
   
   showHideLongitudeFields: function(event) {
    	event.preventDefault();
    	if ($('#radLonConstantOption').is(':checked')){
		  	$('#lon_constant').show();
		  	$('#lon_gridfile').hide();  		
		}
		else if ($('#radLonGridOption').is(':checked')){
		  	$('#lon_constant').hide();
		  	$('#lon_gridfile').show();  		
		}
		else{ // compute option selected
		  	$('#lon_constant').hide();
		  	$('#lon_gridfile').hide();  
		}
   },
   
   showHideTemperatureFields: function(event) {
    	event.preventDefault();
    	if ($('#radTempConstantOption').is(':checked')){
	  		$('#temp_constant').show();
	  		$('#temp_textfile').hide();
	  		$('#temp_gridfile').hide();  		
		}
		else if ($('#radTempTextOption').is(':checked')){
		  	$('#temp_textfile').show();
		  	$('#temp_constant').hide();
		  	$('#temp_gridfile').hide();  		
	    }
		else if ($('#radTempGridOption').is(':checked')){
		  	$('#temp_textfile').hide();
		  	$('#temp_constant').hide();
		  	$('#temp_gridfile').show();  
		}
		else{ //
		  	$('#temp_constant').hide();
		  	$('#temp_textfile').hide();
		  	$('#temp_gridfile').hide();  
		}
   },
   
   showHidePrecipitationFields: function(event) {
    	event.preventDefault();
    	if ($('#radPrecConstantOption').is(':checked')){
	  		$('#prec_constant').show();
	  		$('#prec_textfile').hide();
	  		$('#prec_gridfile').hide();  		
	  	}
	  	else if ($('#radPrecTextOption').is(':checked')){
	  		$('#prec_textfile').show();
	  		$('#prec_constant').hide();
	  		$('#prec_gridfile').hide();  		
	  	}
	  	else if ($('#radPrecGridOption').is(':checked')){
	  		$('#prec_textfile').hide();
	  		$('#prec_constant').hide();
	  		$('#prec_gridfile').show();  
	  	}
	  	else{ //
	  		$('#prec_constant').hide();
	  		$('#prec_textfile').hide();
	  		$('#prec_gridfile').hide();  
	  }
   },
   
   showHideWindFields: function(event) {
    	event.preventDefault();
    	if ($('#radWindConstantOption').is(':checked')){
		  	$('#wind_constant').show();
		  	$('#wind_textfile').hide();
		  	$('#wind_gridfile').hide();  		
		}
	  	else if ($('#radWindTextOption').is(':checked')){
	  		$('#wind_textfile').show();
	  		$('#wind_constant').hide();
	  		$('#wind_gridfile').hide();  		
	  	}
	  	else if ($('#radWindGridOption').is(':checked')){
	  		$('#wind_textfile').hide();
	  		$('#wind_constant').hide();
	  		$('#wind_gridfile').show();  
	  	}
	  	else{ //
	  		$('#wind_constant').hide();
	  		$('#wind_textfile').hide();
	  		$('#wind_gridfile').hide();  
	  	}
   },
   
   showHideRhFields: function(event) {
    	event.preventDefault();
    	if ($('#radRhConstantOption').is(':checked')){
	  		$('#rh_constant').show();
	  		$('#rh_textfile').hide();
	  		$('#rh_gridfile').hide();  		
	  	}
	  	else if ($('#radRhTextOption').is(':checked')){
	  		$('#rh_textfile').show();
	  		$('#rh_constant').hide();
	  		$('#rh_gridfile').hide();  		
	  	}
	  	else if ($('#radRhGridOption').is(':checked')){
	  		$('#rh_textfile').hide();
	  		$('#rh_constant').hide();
	  		$('#rh_gridfile').show();  
	  	}
	  	else{ //
	  		$('#rh_constant').hide();
	  		$('#rh_textfile').hide();
	  		$('#rh_gridfile').hide();  
	  	}
   },
   
   showHideSnowalbFields: function(event) {
    	event.preventDefault();
    	if ($('#radSnowalbConstantOption').is(':checked')){
	  		$('#snowalb_constant').show();
	  		$('#snowalb_textfile').hide();
	  		$('#snowalb_gridfile').hide();  		
	  	}
	  	else if ($('#radSnowalbTextOption').is(':checked')){
	  		$('#snowalb_textfile').show();
	  		$('#snowalb_constant').hide();
	  		$('#snowalb_gridfile').hide();  		
	  	}
	  	else if ($('#radSnowalbGridOption').is(':checked')){
	  		$('#snowalb_textfile').hide();
	  		$('#snowalb_constant').hide();
	  		$('#snowalb_gridfile').show();  
	  	}
	  	else{ //
	  		$('#snowalb_constant').hide();
	  		$('#snowalb_textfile').hide();
	  		$('#snowalb_gridfile').hide();  
	  	}
   },
   
   showHideQgFields: function(event) {
    	event.preventDefault();
    	if ($('#radQgConstantOption').is(':checked')){
	  		$('#qg_constant').show();
	  		$('#qg_textfile').hide();
	  		$('#qg_gridfile').hide();  		
	  	}
	  	else if ($('#radQgTextOption').is(':checked')){
	  		$('#qg_textfile').show();
	  		$('#qg_constant').hide();
	  		$('#qg_gridfile').hide();  		
	  	}
	  	else if ($('#radQgGridOption').is(':checked')){
	  		$('#qg_textfile').hide();
	  		$('#qg_constant').hide();
	  		$('#qg_gridfile').show();  
	  	}
   },
   
   showHideOutputControlFileFields: function(event) {
    	event.preventDefault();
    	if ($('#radDefaultOutputControlFileYes').is(':checked')){  		
  			$('#output_controlfile').hide();
	  	}
	  	else {
	  		$('#output_controlfile').show();	  	
	  	}	
   },
   
   showHideAggrOutputControlFileFields: function(event) {
    	event.preventDefault();
    	if ($('#radDefaultAggrOutputControlFileYes').is(':checked')){  		
  			$('#aggroutput_controlfile').hide();
	  	}
	  	else {
	  		$('#aggroutput_controlfile').show();	  	
	  }	
   }
  };
});