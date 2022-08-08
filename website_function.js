function create_page() {
    document.title = html_format.space_name;
    document.body.style.background = html_format.bg_color;
  
    document.getElementById("space_name").innerHTML = html_format.space_name;
    document.getElementById("availability_message").innerHTML = html_format.availability_message;
    var time = new Date().toLocaleTimeString();
    document.getElementById("current_time").innerHTML = "it is " + time.slice(0,-6) + time.slice(-3);
}