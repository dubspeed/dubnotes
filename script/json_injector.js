var notesData = {
	notes: [
		{
		    id: 1,
			name: "note1",
			text: "this is note nr#5 speaking"
		},
		{
		    id: 2,
			name: "note2",
			text: "note nr 2"
		},
		{
		    id: 3,
			name: "note3",
			text: "umber umber number #3"
		}
	]
};

var note;
var noteName;

var dubnotesSession = {
    "uid": "",
    "oauth_token": ""
};

function fetchNotesFromServer() {
    var data = {};
    if (dubnotesSession.uid != "") {
        data = dubnotesSession;
    }
    $.ajax({
      url: "http://localhost:8080/json/list",
      dataType: 'json',
      data: data,
      success: fetch_success,
      error: fetch_error
    });
} 

function fetch_success (data, textStatus, jqHXR) {
    notesData = data;
    rebuildListView($("#list"), "star");
}

function fetch_error (data, textStatus, jqHXR) {
    // authenticate if we did not fetch
    window.location = "http://localhost:8080/authenticate?url="+$(location).attr('pathname'); //href
}

function fetchOneNote(name) {
    var data={}
    if (dubnotesSession.uid != "") {
        data = dubnotesSession;
    }
    $.ajax({
      url: "http://localhost:8080/json/" + name,
      dataType: 'json',
      data: data,
      success: onenote_success,
      error: fetch_error
    });
}

function onenote_success(data, textStatus, jqHXR) {
    note = data;
    $("#text").html(note.text);
    $("#text").textinput();
}

function findNewNoteName() {
    //TODO: implement
    return "new_note"
}

function addNoteLocal(name, text) {
    var name = findNewNoteName(); 
    notesData.notes = notesData.notes.concat({name:name , text:""});
}

function markupStar() {
    return "<a data-icon='star' data-theme='c' data-rel=\"dialog\" href='#star'></a>"
}

function markupDelete() {
    return "<a data-icon='delete' data-rel=\"dialog\" data-transition=\"pop\" href='#dialog'></a>"
}

function rebuildListView(page, split_identifier) {
    var content = page.children( ":jqmData(role=content)" ),
        markup = "";
    
    for (var i=0; i<notesData.notes.length; i++) {
        var name = notesData.notes[i].name
        markup += "<li>"
        markup += "<a href='#edit#"+name+"'>"+name+"</a>"
        if (split_identifier=="star") { 
            markup += markupStar(); 
        } else {
            markup += markupDelete();
        }
        markup += "</li>";
    }
    content.find( "ul" ).html(markup)
    content.find( ":jqmData(role=listview)" ).listview();
    content.find( ":jqmData(role=listview)" ).listview('refresh');
}

function deactivateButton(button) {
    button.removeClass("ui-btn-active"); //remove active state from button
}

function hideButton(button) {
    button.hide();
}

function showButton(button) {
    button.show();
}

function showNote( urlObj, options )
{
    var page = $("#edit"),
    	markup= "",
    	notename = urlObj.hash.replace( /.*#edit#/, "" );

    /*for (var i=0; i<notesData.notes.length; i++) {
        if (notesData.notes[i].name == notename) {
            markup += notesData.notes[i].text
        }
    }
    
    $("#text").val( markup );
    */
    $("#name").val( notename );
    page.page();
    
    $(".ui-page-active textarea").keyup(); 
    options.dataUrl = urlObj.href;
    $.mobile.changePage( page, options );
}

$(document).bind( "pagebeforechange", function( e, data ) {
	var url_ap = $(location).attr("search");
	if (url_ap.match(/oauth_token/)) {
	    dubnotesSession.uid = url_ap.replace(/\&oauth_token\=.[a-z0-9]*/, "").slice(5);
	    dubnotesSession.oauth_token = url_ap.replace(/\?uid=[0-9]*&oauth_token=/, "")
	    fetchNotesFromServer();  
	}
	
	// We only want to handle changePage() calls where the caller is
	// asking us to load a page by URL.
	if ( typeof data.toPage === "string" ) {
		// $.mobile.path.parseUrl( data.toPage ).hash == "#edit#note1"
		var u = $.mobile.path.parseUrl( data.toPage ),
			re = /^#edit#/;
			
		if ( u.hash.search(re) !== -1 ) {
			fetchOneNote(u.hash.replace(/#edit#/, ""));
			showNote( u, data.options );
			e.preventDefault();
		}
	}
});

$( "#list" ).live( "pagecreate", function( e, data ) {
    var page = $("#list");
    rebuildListView(page, "star");
    hideButton($("#done"));
    page.page();
});
 
$( "#submit" ).live( "click", function(event, ui) {
  name = $("#name").val()
  text = $("#text").val()
  for (var i=0; i<notesData.notes.length; i++) {
      if (notesData.notes[i].name == name) {
          notesData.notes[i].text = text
      }
  }
  event.preventDefault();
  $.mobile.changePage( "#list", { transition: "slide", reverse:true} );
});

$("#new").live ("click", function(event, ui) {
   var page = $("#list");
   addNoteLocal();
   rebuildListView(page, "star");
   deactivateButton($("#new"));
   page.page();
});

$("#delete").live ("click", function(event, ui) {
    var page = $("#list");
    rebuildListView(page, "delete");
    showButton($("#done"));
    page.page();
});

$("#done").live ("click", function(event, ui) {
    hideButton($("#done"));
    deactivateButton($("#delete"));
    rebuildListView($("#list"), "star");
});

$("#sync").live ("click", function(event, ui) {
    event.preventDefault();
    fetchNotesFromServer();
});
