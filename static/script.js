count = 0;
async function getReply(string) {
    try {
        // Perform the POST request asynchronously
        let response = await fetch('/reply', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json', // Set content type to JSON
            },
            body: JSON.stringify({ query: string }) // Send query as part of the request body
        });

        // Check if the response is successful
        if (!response.ok) {
            console.error('Failed to fetch the reply:', response.statusText);
            return; // Exit the function on error
        }

        // Check if the Content-Type indicates JSON
        const contentType = response.headers.get('Content-Type');
        if (contentType && contentType.includes('application/json')) {
            let data = await response.json();

            if (data.redirect) {
                console.log("Redirecting to:", data.redirect);
                
                // Create a form dynamically to submit a POST request
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = data.redirect;

                // Create hidden inputs for topic and flag
                const topicInput = document.createElement('input');
                topicInput.type = 'hidden';
                topicInput.name = 'topic';
                topicInput.value = data.topic;

                const flagInput = document.createElement('input');
                flagInput.type = 'hidden';
                flagInput.name = 'flag';
                flagInput.value = data.id;
                form.appendChild(topicInput);
                form.appendChild(flagInput);
                
                // Append the form to the body and submit it
                document.body.appendChild(form);
				
                form.submit();
            }

            // Use the parsed JSON data here as needed
            console.log('JSON Data:', data);
            return data; // Return data if needed elsewhere
        } else {
            // If the response is not JSON, treat it as text
            let replyString = await response.text(); // Extract the string from the response
            console.log('Reply String:', replyString); // Save the result in a variable and use it
            return replyString; // Return the string if needed elsewhere
        }
    } catch (error) {
        console.error('Error fetching the reply:', error);
    }
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
	botDiv.innerHTML = `<span id="bot-response">${marked.parse(product)}</span>`;
	mainDiv.appendChild(botDiv);

	// Scroll to the bottom after adding new messages
	var scroll = document.getElementById("message-section");
	scroll.scrollTop = scroll.scrollHeight;
}

document.getElementById("send").addEventListener("click", async function() {
	let input = document.getElementById("input").value.trim();
	if (!input) {
		return;
	}

	// Wait for the async getReply to resolve before adding the bot response
	let reply = await getReply(input); // Wait for the promise to resolve
	addChat(input, reply);  // Add the input and reply to the chat

	document.getElementById("input").value = ""; // Clear the input field
});
skip = document.getElementById("skip");
if(skip)
{skip.addEventListener("click", async function() {
	// Wait for the async getReply to resolve before adding the bot response
	let reply = await getReply("skip the basics"); // Wait for the promise to resolve
	addChat("skip the basics", reply);  // Add the input and reply to the chat

	document.getElementById("input").value = ""; // Clear the input field
});}

async function loadChatFromDatabase() {
	try {
		let response = await fetch('/chat_history', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
		});
		if (response.ok) {
			let chatHistory = await response.json();
			const mainDiv = document.getElementById("message-section");

			chatHistory.forEach(chat => {
				let messageDiv = document.createElement("div");
				messageDiv.id = chat.role;
				messageDiv.classList.add("message");
				if(chat.role == 'bot')
				{
					chat.message = marked.parse(chat.message)
				}
				messageDiv.innerHTML = `<span id="${chat.role}-response">${chat.message}</span>`;
				if(count === 0)
				{
					count++;
				}
				else{mainDiv.appendChild(messageDiv);}
			});

			// Scroll to the bottom after loading chat history
			var scroll = document.getElementById("message-section");
			scroll.scrollTop = scroll.scrollHeight;
		} else {
			console.error('Failed to load chat history:', response.statusText);
		}
	} catch (error) {
		console.error('Error loading chat history:', error);
	}
}

// Load chat history when the page is loaded
window.addEventListener("load", function() {
	loadChatFromDatabase();
});