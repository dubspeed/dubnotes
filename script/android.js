if (window.innerWidth && window.innerWidth <= 480) { 
    $(document).ready(function(){ 
        $('#editor').addClass('hide');
        $('#header').append('<div class="leftButton" onclick="toggleMenu()">Menu</div>'); 
        hijacklinks();
    });
    
    function hideMenu() {
        $('#header ul').addClass('hide');
    }
    
    function showEditor() {
        $('#editor').removeClass('hide');
        $('#header .leftButton').removeClass('pressed'); 
    }
    
    function toggleMenu() { 
        $('#header ul').toggleClass('hide'); 
        $('#header .leftButton').toggleClass('pressed'); 
        $('#editor').toggleClass('hide');
    }
    
    function hijacklinks() {
        $('#files a').click(function(e) {
            e.preventDefault();
            hideMenu();
            showEditor();
            $('#editor textarea').load(e.target.href);
            //$('#editor textarea').append("DEBUG: " + e.target.href);
        });
    }
}
