/**
 * Created by pabitra on 6/11/14.
 */
$(document).ready(function(){
    // hookup the buttons to relevant functions
    $('.btn-primary').click(function(){
                var idSplit = new String(this.id).split("_");
                //alert("you clicked " + idSplit[3]);
                if(this.id.indexOf('build_status') > -1){
                    updatePackageStatus(idSplit[3]);
                }
                if(this.id.indexOf('run_status') > -1){
                    updateRunStatus(idSplit[3]);
                }
                else if (this.id.indexOf('retrieve_package-in') > -1) {
                    retrievePackageIn(idSplit[3])
                }
                else if (this.id.indexOf('run_package') > -1) {
                    executeModelPackage(idSplit[3])
                }
                else if (this.id.indexOf('retrieve_package-out') > -1) {
                    retrievePackageOut(idSplit[3])
                }
    })

    $('[id^=lbl_status_]').each(function(){
        if($(this).text().indexOf('Processing') > -1){
            animateProgress(this, $(this).text());
        }
    })

    $('[id^=label_model_pkg_run_status_]').each(function(){
        if($(this).text().indexOf('Processing') > -1){
            animateProgress(this, $(this).text());
        }
    })
})

function updatePackageStatus(pkg_id){
    freezeWindow();

    var statusStyles = {"in_queue": 'aqua', "processing" : 'yellow', "error": 'red', "success": 'lime'};
    var CKAN_Action_URL = '/uebpackage/check_package_build_status/' + pkg_id;
    $.ajaxSetup({
        timeout: 120000 // 120 seconds
    });

    $.getJSON(CKAN_Action_URL)
        .done(function(data) {
            unfreezeWindow();

            alert(data.message);
            if(data.success == true)
            {
                var status_label = '#lbl_status_' + pkg_id;
                var old_status_text = $(status_label).text();
                $(status_label).text("Package build status:" + data.json_data)
                // change the background color
                if(data.json_data === 'In Queue'){
                    $(status_label).css({'background-color':statusStyles.in_queue});
                }
                else if(data.json_data === 'Processing'){
                    $(status_label).css({'background-color':statusStyles.processing});
                    if(old_status_text.indexOf('Processing') == -1){
                        animateProgress(status_label, $(status_label).text());
                    }
                }
                else if(data.json_data === 'Success'){
                    var btn_id = 'btn_retrieve_package-in_' + pkg_id;
                    var label_pkg_availability_status_id = 'lbl_pkg_availability_status_' + pkg_id;

                    var label_html = "<p id=" + label_pkg_availability_status_id  + " style='background-color: aqua'>Package availability status: Ready to retrieve</p>";
                    var btn_html = "<div><button class='btn btn-primary' id=" + btn_id + " name='retrieve' type='submit'>Retrieve Package</button></div>";
                    var div_id = "#div_id_" + pkg_id;
                    $(div_id).append(label_html);
                    $(div_id).append(btn_html);
                    $(status_label).css({'background-color':statusStyles.success});
                    $('#'+btn_id).click(function(){
                        retrievePackageIn(pkg_id);
                    })
                }
                else if(data.json_data === 'Error'){
                    $(status_label).css({'background-color':statusStyles.error});
                }
                // hide the status update button
                var btn_status_update = '#btn_build_status_' + pkg_id;
                if(data.json_data === 'Error' || data.json_data === 'Success'){
                    $(btn_status_update).hide();
                }
            }
            else
            {
                var btn_status_update = '#btn_build_status_' + pkg_id;
                $(btn_status_update).disabled = true;
            }
        })
        .fail(function(jqXHR, textStatus, errorThrown){
            unfreezeWindow();
            var btn_status_update = '#btn_build_status_' + pkg_id;
            $(btn_status_update).disabled = true;
    });

}

function retrievePackageIn(pkg_id){
    freezeWindow();

    var statusStyles = {"not_available": 'mediumpurple', "available" : 'lime', "error": 'red'};
    var CKAN_Action_URL = '/uebpackage/retrieve_input_package/' + pkg_id;
    $.ajaxSetup({
        timeout: 120000 // 120 seconds
    });

    $.getJSON(CKAN_Action_URL)
        .done(function(data) {
            unfreezeWindow();

            alert(data.message);
            var status_label = '#lbl_pkg_availability_status_' + pkg_id;
            $(status_label).text("Package availability status:" + data.json_data)
            if(data.success == true)
            {
                // change the background color
                if(data.json_data === 'Not available'){
                    $(status_label).css({'background-color':statusStyles.not_available});
                }
                else if(data.json_data === 'Available'){
                    $(status_label).css({'background-color':statusStyles.available});
                }
                else if(data.json_data === 'Error'){
                    $(status_label).css({'background-color':statusStyles.error});
                }
                // hide the status update button
                var btn_retrieve_package = '#btn_retrieve_package-in_' + pkg_id;
                if(data.json_data === 'Error' || data.json_data === 'Available'){
                    $(btn_retrieve_package).hide();
                }
            }
            else
            {
                if(data.json_data === 'Error'){
                    $(status_label).css({'background-color':statusStyles.error});
                }
                // hide the status update button
                var btn_retrieve_package = '#btn_retrieve_package-in_' + pkg_id;
                if(data.json_data === 'Error' || data.json_data === 'Available'){
                    $(btn_retrieve_package).hide();
                }
            }
        })
        .fail(function(jqXHR, textStatus, errorThrown){
            unfreezeWindow();
            var btn_retrieve_package = '#btn_retrieve_package-in_' + pkg_id;
            $(btn_retrieve_package).disabled = true;
    });

}

function retrievePackageOut(pkg_id){
    freezeWindow();

    var statusStyles = {"available" : 'lime', "error": 'red'};
    var CKAN_Action_URL = '/uebpackage/retrieve_output_package/' + pkg_id;
    $.ajaxSetup({
        timeout: 120000 // 120 seconds
    });

    $.getJSON(CKAN_Action_URL)
        .done(function(data) {
            unfreezeWindow();

            alert(data.message);
            var status_label = '#label_model_pkg_run_status_' + pkg_id;
            var pkg_type_label = '#label_model_pkg_type_' + pkg_id;
            $(status_label).text("Package run status:" + data.json_data)
            if(data.success == true)
            {
                // change the background color
                if(data.json_data === 'Output package merged'){
                    $(status_label).css({'background-color':statusStyles.available});
                    $(pkg_type_label).text("Package type:Complete");
                }
                else if(data.json_data === 'Error' || data.json_data === 'Failed to retrieve package file' ){
                    $(status_label).css({'background-color':statusStyles.error});
                }
                // hide the status update button
                var btn_retrieve_package = '#btn_retrieve_package-out_' + pkg_id;
                if(data.json_data === 'Error' || data.json_data === 'Output package merged'){
                    $(btn_retrieve_package).hide();
                }
            }
            else
            {
                if(data.json_data === 'Error' || data.json_data === 'Failed to retrieve package file'){
                    $(status_label).css({'background-color':statusStyles.error});
                }
                // hide the status update button
                var btn_retrieve_package = '#btn_retrieve_package-out_' + pkg_id;
                $(btn_retrieve_package).hide();
            }
        })
        .fail(function(jqXHR, textStatus, errorThrown){
            unfreezeWindow();
            var btn_retrieve_package = '#btn_retrieve_package-out_' + pkg_id;
            $(btn_retrieve_package).disabled = true;
    });

}

function executeModelPackage(pkg_id){
    freezeWindow();

    var statusStyles = {"in_queue": 'aqua', "processing" : 'yellow', "error": 'red', "success": 'lime', "output_pkg_available": 'lime', 'not_yet_submitted': 'coral'};
    var CKAN_Action_URL = '/uebpackage/ueb_execute/' + pkg_id;
    $.ajaxSetup({
        timeout: 120000 // 120 seconds
    });

    $.getJSON(CKAN_Action_URL)
        .done(function(data) {
            unfreezeWindow();

            alert(data.message);
            var status_label = '#label_model_pkg_run_status_' + pkg_id;
            $(status_label).text("Package run status:" + data.json_data)
            if(data.success == true)
            {
                // change the background color
                if(data.json_data === 'In Queue'){
                    $(status_label).css({'background-color':statusStyles.in_queue});
                }
                else if(data.json_data === 'Processing'){
                    $(status_label).css({'background-color':statusStyles.processing});
                    animateProgress(status_label, $(status_label).text());
                }
                else if(data.json_data === 'Error'){
                    $(status_label).css({'background-color':statusStyles.error});
                }
                else if(data.json_data === 'Success'){
                    $(status_label).css({'background-color':statusStyles.success});
                }

                if(data.json_data !== 'Error'){
                    var btn_id = 'btn_run_status_' + pkg_id;
                    var btn_html = "<div><button class='btn btn-primary' id=" + btn_id + " name='update' type='submit'>Check Status</button></div>";
                    var div_id = "#div_id_" + pkg_id;
                    $(div_id).append(btn_html);
                    $('#'+btn_id).click(function(){
                        updateRunStatus(pkg_id);
                    })
                }

                // hide the execute button
                var btn_run_package = '#btn_run_package_' + pkg_id;
                if(data.json_data === 'Success' || data.json_data === 'Error' || data.json_data === 'Processing'){
                    $(btn_run_package).hide();
                }
            }
            else
            {
                if(data.json_data === 'Error'){
                    $(status_label).css({'background-color':statusStyles.error});
                }
                // hide the execute button
                var btn_run_package = '#btn_run_package_' + pkg_id;
                if(data.json_data === 'Error'){
                    $(btn_run_package).hide();
                }
            }
        })
        .fail(function(jqXHR, textStatus, errorThrown){
            unfreezeWindow();
            var btn_run_package = '#btn_run_package_' + pkg_id;
            $(btn_run_package).disabled = true;
    });

}

function updateRunStatus(pkg_id){
    freezeWindow();

    var statusStyles = {"in_queue": 'aqua', "processing" : 'yellow', "error": 'red', "success": 'lime', "output_pkg_available": 'lime', 'not_yet_submitted': 'coral'};
    var CKAN_Action_URL = '/uebpackage/ueb_execute_status/' + pkg_id;
    $.ajaxSetup({
        timeout: 120000 // 120 seconds
    });

    $.getJSON(CKAN_Action_URL)
        .done(function(data) {
            unfreezeWindow();

            alert(data.message);
            var status_label = '#label_model_pkg_run_status_' + pkg_id;
            var old_status_text = $(status_label).text();
            $(status_label).text("Package run status:" + data.json_data)
            if(data.success == true)
            {
                // change the background color
                if(data.json_data === 'In Queue'){
                    $(status_label).css({'background-color':statusStyles.in_queue});
                }
                else if(data.json_data === 'Processing'){
                    $(status_label).css({'background-color':statusStyles.processing});
                    if(old_status_text.indexOf('Processing') == -1){
                        animateProgress(status_label, $(status_label).text());
                    }
                }
                else if(data.json_data === 'Error'){
                    $(status_label).css({'background-color':statusStyles.error});
                }
                else if(data.json_data === 'Success'){
                    $(status_label).css({'background-color':statusStyles.success});
                    var btn_id = 'btn_retrieve_package-out_' + pkg_id;
                    var btn_html = "<div><button class='btn btn-primary' id=" + btn_id + " name='retrieve' type='submit'>Retrieve Model Run Output</button></div>";
                    var div_id = "#div_id_" + pkg_id;
                    $(div_id).append(btn_html);
                    $('#'+btn_id).click(function(){
                        retrievePackageOut(pkg_id);
                    })
                }
                else if(data.json_data === 'Not yet submitted'){
                    $(status_label).css({'background-color':statusStyles.not_yet_submitted});
                }
                else if(data.json_data === 'Output package merged'){
                    $(status_label).css({'background-color':statusStyles.output_pkg_available});
                }
                // hide the execute button
                var btn_run_package = '#btn_run_status_' + pkg_id;
                if(data.json_data === 'Success' || data.json_data === 'Error' || data.json_data === 'Output package available'){
                    $(btn_run_package).hide();
                }
            }
            else
            {
                if(data.json_data === 'Error'){
                    $(status_label).css({'background-color':statusStyles.error});
                }
                // hide the execute button
                var btn_run_package = '#btn_run_status_' + pkg_id;
                if(data.json_data === 'Error' || data.json_data === 'Output package available'){
                    $(btn_run_package).hide();
                }
            }
        })
        .fail(function(jqXHR, textStatus, errorThrown){
            unfreezeWindow();
            var btn_run_package = '#btn_run_status_' + pkg_id;
            $(btn_run_package).disabled = true;
    });

}

function animateProgress(label_element, lbl_text){
    var dots = window.setInterval( function() {
        if($(label_element).text().indexOf('Processing') == -1){
            clearInterval(dots);
        }
        else{
            var init_status = lbl_text
            var max_status = lbl_text + ".........."
            if ( $(label_element).text().length > max_status.length )
                $(label_element).text(init_status);
            else
                $(label_element).text($(label_element).text() + ".");
        }
    }, 300);
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