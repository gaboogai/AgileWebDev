var toggle = false;
function toggleText() {
toggle = !toggle;
let text;
if (toggle) {
text = "You pressed the button!";
} else {
text = "";
}
document.getElementById("textBox").innerHTML = text;

fetch('/log_button_press', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ pressed: toggle })
    })
    .then(response => response.json())
    .then(data => {
      console.log('Server response:', data.message);
    })
    .catch(error => {
      console.error('AJAX error:', error);
    });
}

document.addEventListener("keypress", function(event) {
if (event.key === "Enter") {
event.preventDefault();
document.getElementById("myButton").click();
}
});