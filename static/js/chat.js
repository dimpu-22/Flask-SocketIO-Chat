const socket = io();

const typingStatus = document.getElementById("typing-status");

const messages = document.getElementById("messages");

socket.on("online_users", function(data) {
    document.getElementById("online-users").innerHTML =
        "🟢 Online Users: " + data.count;
});

socket.on("receive_message", function(data) {

    const div = document.createElement("div");
    div.className = "message";

    div.innerHTML =
        "<strong>[" + data.time + "] " +
        data.username +
        ":</strong> " +
        data.message;

    messages.appendChild(div);

    // Auto scroll
    messages.scrollTop = messages.scrollHeight;

});

function sendMessage(){

    const username = document.getElementById("username").value;
    const message = document.getElementById("message").value;

    if(message === ""){
        alert("Please enter a message");
        return;
    }

    socket.emit("send_message", {
        username: username,
        message: message
    });

    document.getElementById("message").value = "";
}

let typingTimeout;

document.getElementById("message").addEventListener("input", function () {

    socket.emit("typing", {
        username: document.getElementById("username").value
    });

    clearTimeout(typingTimeout);

    typingTimeout = setTimeout(function () {
        socket.emit("stop_typing");
    }, 1000);

});

socket.on("typing", function (data) {
    typingStatus.innerHTML = data.username + " is typing...";
});

socket.on("stop_typing", function () {
    typingStatus.innerHTML = "";
});