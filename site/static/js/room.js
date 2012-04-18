function RGBtoHex(R,G,B) {return toHex(R)+toHex(G)+toHex(B)}

function toHex(N) {
      if (N==null) return "00";
      N=parseInt(N); if (N==0 || isNaN(N)) return "00";
      N=Math.max(0,N); N=Math.min(N,255); N=Math.round(N);
      return "0123456789ABCDEF".charAt((N-N%16)/16)
           + "0123456789ABCDEF".charAt(N%16);
}

function downloadImage() {
    document.location.href = $("#saved-img").attr("src").replace("image/png", "image/octet-stream");
}
function initWall() {
}

function setColor(color) {
    $(doodleControl.wall_layer).doodle("setColor", color);
    $("#now_color").css("background-color", color);
}

function getNowWidthTop() {
    var width_slider = $("#width_slider");
    return width_slider.width()*(width_slider.val()-width_slider.attr("min"))/width_slider.attr("max")+width_slider.offset().top;
}

function initTool() {
    $(".btn_color").click(function() {
        var color = $(this).css("background-color");
        setColor(color);
    });
    
    $("#now_color").click(function() {
        if ($("#color-picker").css("display") == "none") {
            $("#color-picker").fadeIn(100);
        }
        else {
            $("#color-picker").fadeOut(100);
            $("#now_color").css("background-color", $(doodleControl.wall_layer).data("doodle").color);
        }
        return false;
    });
    $("#color-picker").click(function() {
       return false; 
    });
    $("body").click(function() {
        $("#color-picker").fadeOut(100);
        $("#now_color").css("background-color", $(doodleControl.wall_layer).data("doodle").color);
    });
    color_img = document.getElementById("color-img").getContext('2d');
    var img = new Image();
    img.src = '/static/img/color.jpg';
    img.onload = function() {
        color_img.drawImage(img, 0, 0);
    }
    $("#color-img").bind('mousemove', function(e){
        var offset = $(e.currentTarget).offset();
        var x = e.pageX - offset.left;
        var y = e.pageY - offset.top;
        var imgd = color_img.getImageData(x, y, 1, 1);
        var data = imgd.data;
        var hexString = "#" + RGBtoHex(data[0],data[1],data[2]);
        $("#color-picker input").val(hexString).css("color",hexString);
        $("#now_color").css("background-color", hexString);
        return false;
    });
    $("#color-img").click(function() {
        setColor($("#now_color").css("background-color"));
        $("#color-picker").fadeOut(100);
    });
    $("#color-picker input").keypress(function(e) {
        if (e.which == 13) {
            setColor($(this).val());
            $("#color-picker").fadeOut(100);
        }
    });


    $("#slider").hover(function() {
        $("#now_width").css({
            "top" : getNowWidthTop(),
            "left" : $("#width_slider").offset().left-20,
        }).fadeIn(100);
    }, function() {
        $("#now_width").fadeOut(1000);
    });
    $("#width_slider").change(function() {
        $(doodleControl.wall_layer).doodle("setWidth", $(this).val());
        $("#now_width").html($(this).val()).css("top",getNowWidthTop());
    });
}

function initControl() {
    $("#btn_save").click(function() {
        //showLoading
        var dataUrl = document.getElementById("public_layer").toDataURL();
        $("#btn_save").button('loading');

        $.ajax({
            type: "POST",
            url: "save/",
            data: {"data":dataUrl,  "_xsrf": getCookie("_xsrf")},
            dataType: "json",
            async: true,
            success: function() {
                $("#btn_save").button('reset');
                $("#saved-img").attr("src", dataUrl);
            }
        });
    });
}
    
$(document).ready(function() {
    initTool();  
    initControl();   
});
$(window).load(function() {
    $(doodleControl.public_layer).doodle("load", $("#saved-img").attr("src")); 
});