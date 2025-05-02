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
}
document.addEventListener("keypress", function(event) {
if (event.key === "Enter") {
event.preventDefault();
document.getElementById("myButton").click();
}
});