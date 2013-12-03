	  var ShapeFileType = {Point: 'Point', Stream: 'Stream', Watershed: 'Watershed'};
      var outletPointShape = null;
      var outletPointShapeMarker = null;
      var streamShapeArray = new Array();
      var watershedShape = null;
      var gmap = null;
      var outletLat = null;
      var outletLon = null;
      var isMapInDragMode = false;

      function initialize() {
        var mapOptions = {
				          center: new google.maps.LatLng(38, -97),
				          zoom: 5,
				          scaleControl: true,
				          draggable: false,
				          mapTypeId: google.maps.MapTypeId.TERRAIN
				        };
        
        gmap = new google.maps.Map(document.getElementById("gmap"), mapOptions);
        
        google.maps.event.addListener(gmap, 'click', function(event){

                    if(isMapInDragMode == true)
                    {
                        isMapInDragMode = false;
                        return;
                    }

                	removeAllShapes();                                       
                    document.getElementById("lat").value = event.latLng.lat();
                    document.getElementById("lon").value = event.latLng.lng();                    
                    document.getElementById("btn_delineate").disabled = false;                                                            
	    			document.getElementById("btn_downloadshapefile").disabled = true;
	    			document.getElementById("btn_save_as_CKAN_resource").disabled = true;
	    	
                    var currentZoomLevel = gmap.getZoom();
                    markSelectedOutletPointOnMap(event.latLng.lat(), event.latLng.lng(), currentZoomLevel);

                    // change the cursor to pointer
                    gmap.setOptions({draggable : false});
                
       		});

       	google.maps.event.addListener(gmap, 'mousedown', function(event){
       		            gmap.setOptions({draggable : true});
       	});

        google.maps.event.addListener(gmap, 'drag', function(event){
       		          isMapInDragMode = true;

       	});

       	google.maps.event.addListener(gmap, 'dragend', function(event){
       		          gmap.setOptions({draggable : false});

       	});

      }

      document.getElementById('spinner').style.visibility = 'hidden';
      document.getElementById("btn_delineate").disabled = true;	    	
	  document.getElementById("btn_downloadshapefile").disabled = true;
	  document.getElementById("btn_save_as_CKAN_resource").disabled = true;
	    	
      google.maps.event.addDomListener(window, 'load', initialize);      

      function markSelectedOutletPointOnMap(lat, lon, zoomLevel)
      {
      	var shapeStrokeColor = "#190707"; // default black
      	/*
      	 * icon: {
                                  path: google.maps.SymbolPath.CI,
                                  strokeColor: shapeStrokeColor,
                                  scale: 2
                                },
      	 */
      	if(outletPointShapeMarker != null)
        {
            outletPointShapeMarker.setMap(null);
            outletPointShapeMarker = null;
        }
        
      	outletPointShapeMarker = new google.maps.Marker({
                                position: new google.maps.LatLng(lat, lon),                                
                                draggable: false,
                                title: "Lat:" + lat + "and Lon:" + lon
                              });

      	outletPointShapeMarker.setMap(gmap);
      	gmap.setZoom(zoomLevel);
      	gmap.setCenter(new google.maps.LatLng(lat, lon));
      }
      
      function showAllShapeFilesOnMap()
        {   
            //show outlet point first
            showShapeOnMap("Watershedpoint", ShapeFileType.Point, function(){
                //then show watershed boundary
                showShapeOnMap("Watershed", ShapeFileType.Watershed, function(){
                    //then show stream flow lines - uncomment the 3 lines below to show stream lines
                    //showShapeOnMap("Stream", ShapeFileType.Stream, function(){
                        //unfreezeWindow();
                    //});
                });
            });
            
            markSelectedOutletPointOnMap(outletLat, outletLon, 10);
        }
        
		function removeAllShapes()
		{            
		    if(outletPointShapeMarker != null)
		        {
		            outletPointShapeMarker.setMap(null);
		            outletPointShapeMarker = null;
		        }
		    if(outletPointShape != null)
		        {
		            outletPointShape.setMap(null);
		            outletPointShape = null;
		        }
		    if(watershedShape != null)
		        {
		            watershedShape.setMap(null);
		            watershedShape = null;
		        }
		    if(streamShapeArray.length != 0)
		        {
		            for(var i=0; i< streamShapeArray.length; i++)
		                {
		                    streamShapeArray[i].setMap(null);
		                }
		        }
		} 
       
	  function delineateWatershed()
	  {
	  		freezeWindow();
	  		document.getElementById('spinner').style.visibility = 'visible'; 
			document.getElementById("btn_delineate").disabled = true; 
			outletLat = document.getElementById("lat").value;
			outletLon = document.getElementById("lon").value;
			var CKAN_Action_URL = '/delineate/delineate_ws/' + outletLat +'/' + outletLon;
			$.ajaxSetup({
                timeout: 120000 // 120 seconds
            });

			$.getJSON(CKAN_Action_URL)
		   		.done(function(data) { 	           			
		   			document.getElementById('spinner').style.visibility = 'hidden'; 
					unfreezeWindow();
				
					alert(data.message);
					if(data.success == true)
					{	
						//showalert(data.message, "alert-success");
						document.getElementById("btn_downloadshapefile").disabled = false;
						document.getElementById("btn_save_as_CKAN_resource").disabled = false;
						showAllShapeFilesOnMap();	           				
					}
					else
					{
						//showalert(data.message, "alert-error");
						document.getElementById("btn_delineate").disabled = false;					    	
				    	document.getElementById("btn_downloadshapefile").disabled = true;
				    	document.getElementById("btn_save_as_CKAN_resource").disabled = true;
					}	           			    			
				})
				.fail(function(jqXHR, textStatus, errorThrown){
					document.getElementById('spinner').style.visibility = 'hidden'; 
					unfreezeWindow();
					document.getElementById("btn_delineate").disabled = false;
					if(textStatus == "timeout")
					{
					    alert("Server timeout. This may be too big a watershed." + '\n' + "Try a different outlet location.");
					}
					else
					{
					    alert('Delineation failed.' +'\n' + "Try a different outlet location.");
					}

		    }); 
	        
	  } 
	     
	  //this one for showing a shape on google map
	  //using our own web service API to get the lat/lon sets of values
	  //for a given shapefile
	  function showShapeOnMap(shapeFileName, shapeFileType, callback)
      {            
            // a random number is added to the end of the actual query string
            // to avoid IE caching the ajax response content
            // Ref: http://viralpatel.net/blogs/ajax-cache-problem-in-ie/
            // var showShapePageUrl = 'index.php?option=com_gmap&task=showshape' + "&random=" + Math.random();
            var CKAN_Action_URL = '/delineate/showWatershed/' + shapeFileName;            
           	$.getJSON(CKAN_Action_URL)           		
           		.done(function(data) { 
           			if(data.success == true)
           			{
           			    addShapeToMap(JSON.parse(data.json_data), shapeFileType);
           			    callback();
           			}
           			else
           			{
           			    alert(data.message);
           			}
           		})
           		.fail(function(jqXHR, textStatus, errorThrown){
           			alert('Request for getting lat/lon values for shape file display failed! ' + textStatus);
           		});  
      }
        
      function addShapeToMap(latLonValuesJS_Object, shapeFileType)
      {            
            var latLonForAllShapes = latLonValuesJS_Object;
            //iterate each set of lat/lon values
            var shapeStrokeColor = "#190707"; // default black
            var strokeWeight = 2;
            if(shapeFileType == ShapeFileType.Point)
            {
                shapeStrokeColor = "#190707"; // black
                strokeWeight = 5;
                var latLonValuesShape = latLonForAllShapes[0];
                var latLonValue = latLonValuesShape.LatlonValues[0];
                outletLat = latLonValue.Lat;
                outletLon = latLonValue.Lon;
                outletPointShape = new google.maps.Marker({
                            position: new google.maps.LatLng(latLonValue.Lat, latLonValue.Lon),
                            icon: {
                              path: google.maps.SymbolPath.CIRCLE,
                              strokeColor: shapeStrokeColor,
                              scale: 2
                            },
                            draggable: false
                          });

                outletPointShape.setMap(gmap);
            }
            else if(shapeFileType == ShapeFileType.Stream)
            {
                shapeStrokeColor = "#0000FF"; // blue
                streamShapeArray = new Array();
                for(var i=0; i < latLonForAllShapes.length; i++)
                {
                    var latLonValuesShape = latLonForAllShapes[i];
                    var lineCoordinates = new Array();
                    for(var j=0; j < latLonValuesShape.LatlonValues.length; j++)
                    {
                        var latLonValue = latLonValuesShape.LatlonValues[j];
                        lineCoordinates.push(new google.maps.LatLng(latLonValue.Lat, latLonValue.Lon));
                    }
                    var streamShape = new google.maps.Polyline({
                                    path: lineCoordinates,
                                    strokeColor: shapeStrokeColor,
                                    strokeOpacity: 1.0,
                                    zIndex: 1,
                                    strokeWeight: strokeWeight
                                  });

                    streamShape.setMap(gmap);
                    streamShapeArray.push(streamShape);
                }
            }
            else if(shapeFileType == ShapeFileType.Watershed)
            {
                shapeStrokeColor = "#DF0101"; // green
                var lineCoordinates = new Array();
                for(var i=0; i < latLonForAllShapes.length; i++)
                {
                    var latLonValuesShape = latLonForAllShapes[i];
                    for(var j=0; j < latLonValuesShape.LatlonValues.length; j++)
                    {
                        var latLonValue = latLonValuesShape.LatlonValues[j];
                        lineCoordinates.push(new google.maps.LatLng(latLonValue.Lat, latLonValue.Lon));
                    }
                }
                
                watershedShape = new google.maps.Polygon({
                                    paths: lineCoordinates,
                                    strokeColor: shapeStrokeColor,
                                    strokeOpacity: 0.8,
                                    strokeWeight: 2,
                                    fillColor: "#D8D8D8", //light gray
                                    fillOpacity: 0.65
                                  });

                watershedShape.setMap(gmap);
            }
      }            
       	
	function downloadShapeFile()
	{
	    //file download can be done only through href link            
	    var link = document.getElementById("downloadShapeFilesLink");
	    link.click();            
	}
        
	function showSaveFileDialog()
	{
		$('#saveFileModal').css('z-index', 1050);		
		$('#saveFileModal').modal('show');
	}
    
    //saves the delineated watershed shape file as a CKAN resource  
	function saveShapeFile() 
	{                        
		var shapeFileName = $('#field-shapefilename').val();
		var watershedDescription = $('#field-shapefiledescription').val();
		if(shapeFileName.length == 0 || watershedDescription.length == 0)
		{
			return;
		}
		else
		{
			$('#saveFileModal').css('z-index', -1);
			$('#saveFileModal').modal('hide');
			$('#field-shapefilename').val('');
			$('#field-shapefiledescription').val('');
		}				
		
		document.getElementById("btn_save_as_CKAN_resource").disabled = true; 
		outletLat = document.getElementById("lat").value;
	  	outletLon = document.getElementById("lon").value;
	    var CKAN_Action_URL = '/delineate/saveshapefile/' + outletLat +'/' + outletLon + '/' + shapeFileName + '/' + watershedDescription;
	    
	   	$.getJSON(CKAN_Action_URL)           		
	   		.done(function(data) { 	           			
	   			if(data.success == true)
	   			{
	   			    alert('Watershed shape file was saved as a resource.');
	   			}
	   			else{
	   			    alert(data.message);
	   			    document.getElementById("btn_save_as_CKAN_resource").disabled = false;
	   			}
	   		})
	   		.fail(function(jqXHR, textStatus, errorThrown){
	   			document.getElementById("btn_save_as_CKAN_resource").disabled = false;
	   			if(errorThrown == 'Not Found')
	   			{
	   			    alert('Invalid file name or description.');
	   			}
	   			else
	   			{
	   			    alert('Failed to save the shape file as a resource.' +'\n' + textStatus);
	   			}
	       	});  
		                            
	}
        
	function freezeWindow()
	{
	    var freezeDiv = document.createElement("div");
	    freezeDiv.id = "freezeDiv";
	    freezeDiv.style.cssText = "position:absolute; top:0; right:0; width:" + screen.width + "px; height:" + screen.height + "px; background-color: #000000; opacity:0.5; filter:alpha(opacity=50)";
	    document.getElementsByTagName("body")[0].appendChild(freezeDiv );
	}
	
	function unfreezeWindow()
	{
	     var freezeDiv = document.getElementById("freezeDiv");
	     document.getElementsByTagName("body")[0].removeChild(freezeDiv );
	}
        
    /**
	Bootstrap Alerts -
	Function Name - showalert()
	Inputs - message,alerttype
	Example - showalert("Invalid Login","alert-error")
	Types of alerts -- "alert-error","alert-success","alert-info"
	Required - You only need to add a alert_placeholder div in your html page wherever you want to display these alerts "<div id="alert_placeholder"></div>"
	Written On - 14-Jun-2013
	**/
	function showalert(message,alerttype) 
	{

    	$('#alert_placeholder').append('<div id="alertdiv" class="alert ' +  alerttype + '"><a class="close" data-dismiss="alert">×</a><span>'+message+'</span></div>')

		setTimeout(function() { // this will automatically close the alert and remove this if the users doesnt close it in 5 secs


  		$("#alertdiv").remove();

    	}, 5000);
	}