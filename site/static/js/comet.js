$(document).ready(function() {
    chatControl.init();
    doodleControl.init();
    onlineControl.init();
    comet.init();
});

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function guidGenerator() {
    var S4 = function() {
       return (((1+Math.random())*0x10000)|0).toString(16).substring(1);
    };
    return (S4()+S4()+"-"+S4()+"-"+S4()+"-"+S4()+"-"+S4()+S4()+S4());
}

jQuery.fn.disable = function() {
    this.enable(false);
    return this;
};

jQuery.fn.enable = function(opt_enable) {
    if (arguments.length && !opt_enable) {
        this.attr("disabled", "disabled");
    } else {
        this.removeAttr("disabled");
    }
    return this;
};

var chatControl = {
    form : "#messageform",
    input : "#message",
    inbox : "#inbox",
    
    init: function() {
        $(chatControl.form).live("submit", function() {
            chatControl.create();
            return false;
        });
        $(chatControl.form).live("keypress", function(e) {
            if (e.keyCode == 13) {
                if ($(chatControl.input).val()=="") return false;
                chatControl.create();
                return false;
            }
        });
        $(chatControl.input).select();
    },
    
    create: function() {
        var message = {
            "id": guidGenerator(),
            "type": "chat",
            "content": $(chatControl.input).val(),
            "user": $("#userpanel .dropdown a span").html()
        }
        $(chatControl.form).find("input[type=submit]").disable();
        comet.send(message);
    },
    
    show: function(message) {
        var existing = $("#m" + message.id);
        if (existing.length > 0) return;
        var node = $('<div id="#m'+message.id+'"><strong>'+message.user+'</strong>: '+message.content+'</div>');
        node.hide();
        $(chatControl.inbox).append(node);
        node.fadeIn();
        document.getElementById("inbox").scrollTop = 999999999;
    }
};
var onlineControl = {
    init: function() {
        $(window).bind('beforeunload', function() {
            /* server had create an online message, so here needn't to create another one*/
            onlineControl.create(false);
        });
    },
    create: function(status) {
        var message = {
            "id": guidGenerator(),
            "type": "online",
            "content": status
        }
        if (status==false) comet.send(message, false);
    },
    show: function(message) {
        var existing = $("#m" + message.id);
        if (existing.length > 0) return;
        var status;
        if (message.content) status = "enter";
        else status = "left"
        var node = $('<div id="#m'+message.id+'"><strong>'+message.user.name+'</strong> '+status+' the room</div>');
        node.hide();
        $(chatControl.inbox).append(node);
        node.fadeIn();
        document.getElementById("inbox").scrollTop = 999999999;

        if (message.content == true) {
            $(".room-online-num").html(parseInt($(".room-online-num").html())+1);
            $("#online-box").append('<a id="uo'+ message.user.id +'" href="/people/'+message.user.url+'/" rel="twipsy" data-original-title="'+message.user.name+'" class="user-hangout"><img src="'+message.user.icon+'"></a> ');  
        }
        else {
            $(".room-online-num").html(parseInt($(".room-online-num").html())-1);
            $("#uo"+message.user.id).remove();
        }
    }
    
}

function doodleOnMouseUp(points, color, width) {
    doodleControl.create(points, color, width);
}
var doodleControl = {
    wall_layer: "#wall_layer",
    public_layer: "#public_layer",
    
    init: function() {
        $(doodleControl.wall_layer).doodle({onMouseUp: doodleOnMouseUp});
        $(doodleControl.public_layer).doodle({canMouseDraw: false});
    },
    create: function(points, color, width) {
        var message = {
            "id": guidGenerator(),
            "type": "doodle",
            "points": points,
            "color": color,
            "width": width
        };
        comet.send(message, true, function() {
        });
    },
    show: function(message) {
        $(doodleControl.public_layer).doodle("draw", message.points, message.color, message.width);
        $(doodleControl.wall_layer).doodle("clear");
    }
};
var comet = {
    sendUrl: "message/new/",
    pollUrl: "message/updates/",
    initUrl: "message/init/",
    errorSleepTime: 500,
    update_time: null,

    send: function(data, async, callback) {
        $.ajax({
            url: comet.sendUrl, 
            data: {
                "message": $.toJSON(data),
                "_xsrf": getCookie("_xsrf")
            },
            dataType: "json",
            async: async, 
            type: "POST",
            success: function(response) {
                if (callback) callback(response);
            }, 
            error: function(response) {
                console.log("ERROR:", response);
            }
        });
    },
    
    poll: function(update_time) {
        var args = {"_xsrf": getCookie("_xsrf")}
        if (comet.update_time) args.update_time = comet.update_time
        $.ajax({
            url: comet.pollUrl,
            data: args,
            type: "POST",
            dataType: "json",
            success: comet.onSuccess,
            error: comet.onError
        });
    },
    
    init: function(cursor) {
        var args = {"_xsrf": getCookie("_xsrf")};
        $.ajax({
            url: comet.initUrl, 
            type: "POST", 
            dataType: "json",
            data: args, 
            success: comet.onSuccess,
            error: comet.onError
        });
    },
    
    onSuccess: function(response) {
        try {
            comet.update_time = new Date().getTime();
            if (!response.messages) return;
            var messages = response.messages;
            for (var i = 0; i < messages.length; i++) {
                if (messages[i].type == "chat") {
                    chatControl.show(messages[i]);
                }
                else if (messages[i].type == "doodle") {
                    doodleControl.show(messages[i]);
                }
                else if (messages[i].type == "online") {
                    onlineControl.show(messages[i]);
                }
            }
        } 
        catch (e) {
            comet.onError();
            return;
        }
        comet.errorSleepTime = 500;
        window.setTimeout(comet.poll, 0);
    },

    onError: function(response) {
        comet.errorSleepTime *= 2;
        window.setTimeout(comet.poll, comet.errorSleepTime);
    }
};
