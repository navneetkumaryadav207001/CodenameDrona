let expectedReply = [
	["Hi, how are you?", "I'm good, thanks!"],
	["What's your name?", "My name is Chatbot"],
	["Goodbye", "Goodbye, have a nice day!"]
];

let expectedMessage = [
	["hi", "hello", "hey"],
	["what is your name", "your name"],
	["bye", "goodbye", "see you later"]
];

function getReply(string) {
	let item;
	for (let x = 0; x < expectedMessage.length; x++) {
		if (expectedMessage[x].includes(string)) {
			items = expectedReply[x];
			item = items[Math.floor(Math.random() * items.length)];
		}
	}
	return item;
}

function addChat(input, product) {
	const mainDiv = document.getElementById("message-section");
	let userDiv = document.createElement("div");
	userDiv.id = "user";
	userDiv.classList.add("message");
	userDiv.innerHTML = `<span id="user-response">${input}</span>`;
	mainDiv.appendChild(userDiv);

	let botDiv = document.createElement("div");
	botDiv.id = "bot";
	botDiv.classList.add("message");
	botDiv.innerHTML = `<span id="bot-response">${product}</span>`;
	mainDiv.appendChild(botDiv);
	var scroll = document.getElementById("message-section");
	scroll.scrollTop = scroll.scrollHeight;
}

document.getElementById("send").addEventListener("click", function() {
	let input = document.getElementById("input").value.trim();
	if (!input) {
		return;
	}
	addChat(input, getReply(input));
	document.getElementById("input").value = "";
});