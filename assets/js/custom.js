var socket;
var disable_requests = false;

function enable_requests(){
    disable_requests = false;
}

function add_url(){
    var x;
    var stream_url = prompt("Please input new stream url:","");
    if (stream_url != null){
        redirect_url = '/?action=add&url="' + encodeURI(stream_url) + '"';
        window.location.href = redirect_url;
    }
}

document.getElementById("file_upload").onchange = function() {
    document.getElementById("pls_upload_frm").submit();
};

function send_cmd(command, item_id){
    if(!disable_requests){
        socket.emit('command', command, item_id);
        disable_requests = true;
        setTimeout(enable_requests, 1000);
    }
}

function volume_up(){
    send_cmd('vol_up', 0);
}

function volume_down(){
    send_cmd('vol_dn', 0);
}

function mpc_stop(){
    send_cmd('mpc_stop', 0);
}

function mpc_play(id){
    send_cmd('mpc_play', id);
}

function mpc_save(){
    send_cmd('mpc_save', 0);
}

function mpc_title(){
    send_cmd('mpc_title', 0);
}

(function() {
    socket = io.connect('http://' + document.domain + ':' + location.port);

    socket.on('playlist', function(msg) {
        var data = JSON.parse(msg);

        if (data.hasOwnProperty("song_title")){
            document.getElementById("song_title").innerHTML = data["song_title"];
        }

        if (data.hasOwnProperty("items") && data.hasOwnProperty("current")){
            var list = document.getElementById("mpc_pls");
            list.innerHTML = "";
            var items = data["items"];
            var current = data["current"];

            for(var i = 0; i < items.length; i++) {
                var item_data = items[i];
                var item = document.createElement('li');
                if(item_data['id'] == current){
                    item.classList.add("active_stream");
                }
                item.innerHTML = "<p class='url_name' onclick='mpc_play(" + item_data['id'] + ")'>" + item_data['name'] + "</p>" +
                                "<span class='url_ctrl'>" +
                                "<a href='/?id=" + item_data['id'] + "&action=del'><i class='fa fa-trash'></i></a>" +
                                "</span>";
                list.appendChild(item);
            }
        }
    });

    window.setInterval(mpc_title, 10000);

})();
