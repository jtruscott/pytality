/*
    Screen.js - Functionality for blitting CP437-style ASCII art and text
    in a browser, using <canvas> and images.
*/

//screen dimensions
var rows = 60;
var cols = 120;

//character dimensions
var W = 8;
var H = 12;

//images of characters 0-255, one per color
var bg_image_file = "images/colors.png";
var char_image_files = [
    "images/char/0.png",
    "images/char/1.png",
    "images/char/2.png",
    "images/char/3.png",
    "images/char/4.png",
    "images/char/5.png",
    "images/char/6.png",
    "images/char/7.png",
    "images/char/8.png",
    "images/char/9.png",
    "images/char/10.png",
    "images/char/11.png",
    "images/char/12.png",
    "images/char/13.png",
    "images/char/14.png",
    "images/char/15.png"
];
var bg_image;
var char_images = [];

function set_message(msg) {
    var msg = $("<div>" + msg + "</div>");
    $("#message_zone").append(msg);
    msg.fadeOut(10000);
}

function preload_images() {
    function img(src) {
        var image = $('<img style="height: 0px; width: 0px" src="' + src + '">');
        $("body").append(image);
        return image.get(0);
    }
    set_message("Loading Images...");
    bg_image = img(bg_image_file);
    for(var i = 0; i < char_image_files.length; i++) {
        char_images.push(img(char_image_files[i]));
    }
}

//drawImage(image, sx, sy, sWidth, sHeight, dx, dy, dWidth, dHeight)
function flip_cells() {
    var cell_changes = window.cell_changes;
    for(var i = 0; i < cell_changes.length; i++) {
        var cell = cell_changes[i];
        var r = cell[0], 
            c = cell[1],
            bg = cell[2],
            fg = cell[3],
            ord = cell[4];
        //draw the bg
        buffer_ctx.drawImage(bg_image, (bg*W), 0, W, H, (c*W), (r*H), W, H);
        //draw the fg
        buffer_ctx.drawImage(char_images[fg], ((ord%16)*W), (parseInt(ord / 16, 10)*H), W, H, (c*W), (r*H), W, H);
    }
    screen_ctx.drawImage(buffer, 0, 0);
}

function reset_cells() {
    buffer_ctx.fillRect(0, 0, buffer.width, buffer.height);
    screen_ctx.drawImage(buffer, 0, 0);

}

var scr;
var buffer;
var screen_ctx;
var buffer_ctx;

function create_screen() {
    set_message("Creating screen...");
    //build up a screen
    scr = $('<canvas id="Screen" width="' + cols*W + '" height="' + rows*H + '">Support for HTML5 Canvas is required.</canvas>');
    $("body").append(scr);
    var canvas = scr.get(0);
    if(!canvas.getContext)
        alert("Support for HTML5 Canvas is required.");
    
    screen_ctx = canvas.getContext('2d');

    buffer = document.createElement('canvas');
    buffer.width = canvas.width; buffer.height = canvas.height;
    buffer_ctx = buffer.getContext('2d');
}

var input_queue = [];

function setup_input_handler() {
    set_message("Setting up input handlers...");
    $(document).keydown(function(e) {
        if(input_queue.length > 1) {
            //prevent a traffic jam
            return;
        }
        input_queue.push(e.which);
    });
}

function set_title(title) {
    $("title").text(title);
}

$(function() {
    $("#message_zone div").fadeOut(20000);
    preload_images();
    create_screen();
    set_message("Waiting for Python...");
    $(document).click(function() {
        set_message("This is a text console game. It does not use the mouse.");
    });

});
