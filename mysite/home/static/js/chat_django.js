const markdown = window.markdownit()

const API_BASE_URL = 'http://127.0.0.1:8000/api';
const API_URL = 'http://127.0.0.1:8000/chat/';

const message_box = document.getElementById(`messages`);
const box_conversations = document.querySelector(`.top`);
const pdf_upload_form = document.querySelector('#pdf-upload-form');

const message_id = () => {
	random_bytes = (Math.floor(Math.random() * 1338377565) + 2956589730).toString(
		2
	);
	unix = Math.floor(Date.now() / 1000).toString(2);

	return BigInt(`0b${unix}${random_bytes}`).toString();
};

const getConversations = async () => {
    const response = await fetch(`${API_BASE_URL}/conversations/`);
    return await response.json();
};

const getConversation = async (conversation_id) => {
    const response = await fetch(`${API_BASE_URL}/conversation/${conversation_id}/`);
    return await response.json();
};

const addConversation = async (conversation_id, title) => {
    console.log(`${API_BASE_URL}/add_conversation/`)
    await fetch(`${API_BASE_URL}/add_conversation/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: conversation_id, title: title }),
    });
};

const addMessage = async (conversation_id, role, content) => {
    await fetch(`${API_BASE_URL}/add_message/${conversation_id}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ role: role, content: content }),
    });
};

const deleteConversation = async (conversation_id) => {
    await fetch(`${API_BASE_URL}/delete_conversation/${conversation_id}/`, {
        method: 'DELETE',
    });
};

const clear_conversation = async () => {
	let messages = message_box.getElementsByTagName(`div`);
	while (messages.length > 0) {
		message_box.removeChild(messages[0]);
	}
};
const clear_conversations = async () => {
	const elements = box_conversations.childNodes;
	let index = elements.length;

	if (index > 0) {
		while (index--) {
			const element = elements[index];
			if (
				element.nodeType === Node.ELEMENT_NODE &&
				element.tagName.toLowerCase() !== `button`
			) {
				box_conversations.removeChild(element);
			}
		}
	}
};

const set_conversation = async (conversation_id) => {
	window.conversation_id = conversation_id;
    console.log(conversation_id)
    disable_form();
	await clear_conversation();
	await load_conversation(conversation_id);
	// await load_conversations(20, 0, true);
};

const show_option = async (conversation_id) => {
	const conv = document.getElementById(`conv-${conversation_id}`);
	const yes = document.getElementById(`yes-${conversation_id}`);
	const not = document.getElementById(`not-${conversation_id}`);

	conv.style.display = "none";
	yes.style.display = "block";
	not.style.display = "block";
}
const hide_option = async (conversation_id) => {
	const conv = document.getElementById(`conv-${conversation_id}`);
	const yes = document.getElementById(`yes-${conversation_id}`);
	const not = document.getElementById(`not-${conversation_id}`);

	conv.style.display = "block";
	yes.style.display = "none";
	not.style.display = "none";
}

const load_conversations = async (limit, offset, loader) => {
    const conversations = await getConversations();
    console.log(conversations)
    // await clear_conversations();

    for (const conversation of conversations) {
        box_conversations.innerHTML += `
            <div class="convo" id="convo-${conversation.id}">
                <div class="left" onclick="set_conversation('${conversation.id}')">
                    <i class="fa-regular fa-comment blue"></i>
                    <span class="convo-title">${conversation.title}</span>
                </div>
                <i onclick="show_option('${conversation.id}')" class="fa-regular fa-trash red" id="conv-${conversation.id}"></i>
                <i onclick="delete_conversation('${conversation.id}')" class="fa-regular fa-check red" id="yes-${conversation.id}" style="display:none;"></i>
                <i onclick="hide_option('${conversation.id}')" class="fa-regular fa-x" id="not-${conversation.id}" style="display:none;"></i>
            </div>
        `;
    }
};

const load_conversation = async (conversation_id) => {
    const messages = await getConversation(conversation_id);
    let i = 0;
    for (const item of messages) {
        message_box.innerHTML += `
            <div class="${item.role == "assistant" ? `message bot-message` : `message user-message`} " style="--j: ${i};">
                <div class="content">
                    ${markdown.render(item.content)}
                </div>
                <div class="user">
                    ${item.role == "assistant" ? "" : user_image}
                </div>
            </div>
        `;
        i += 1;
    }
};

const add_conversation = async (conversation_id, title) => {
    await addConversation(conversation_id, title);
};

const add_message = async (conversation_id, role, content) => {
    await addMessage(conversation_id, role, content);
};

const uuid = () => {
	return `xxxxxxxx-xxxx-4xxx-yxxx-${Date.now().toString(16)}`.replace(
		/[xy]/g,
		function(c) {
			var r = (Math.random() * 16) | 0,
				v = c == "x" ? r : (r & 0x3) | 0x8;
			return v.toString(16);
		}
	);
};

const disable_form = () => {
    pdf_upload_form.style.display = 'none';
}
const enable_form = () => {
    pdf_upload_form.style.display = 'block';
}

const new_conversation = async () => {
	window.conversation_id = uuid();
    enable_form();
	await clear_conversation();

    message_box.innerHTML += `
    <div class="itemsrow" id="homepage-items">
        <div class="examples">
            <button class="button-custom">"Explain quantum computing in simple terms"</button>
            <button class="button-custom">"Got any creative ideas for a 10 year old’s birthday?"</button>
        </div>
    </div>
    `;
};

const delete_conversation = async (conversation_id) => {
    await deleteConversation(conversation_id);
    if (window.conversation_id == conversation_id) {
        await new_conversation();
    }
    await clear_conversations();
    await load_conversations(20, 0, true);
};

const ask_gpt = async (message) => {
    message_input.value = ``;
    message_input.innerHTML = ``;
    message_input.innerText = ``;

    const get_conv = await getConversation(window.conversation_id);
    if(get_conv && get_conv.error){
        console.log("New Conversation");
        await add_conversation(window.conversation_id, message.substr(0, 22));
        await clear_conversation();
        await clear_conversations();
        await load_conversations();
    }

    window.token = message_id();

    let newMessage = document.createElement("div");
    newMessage.classList.add("message", "user-message");
    newMessage.innerHTML = `
        <div class="content" id="user_${token}"> 
            ${message}
        </div>
        <div class="user">
            ${user_image}
        </div>
    `;
    message_box.appendChild(newMessage);

    await new Promise((r) => setTimeout(r, 500));

    let newMessage_bot = document.createElement("div");
    newMessage_bot.classList.add("message", "bot-message");
    newMessage_bot.innerHTML = `
        <div class="content" id="gpt_${window.token}">
            <div id="cursor"></div>
        </div>
    `;
    message_box.appendChild(newMessage_bot);
    console.log(window.token)

    await new Promise((r) => setTimeout(r, 1000));
    window.scrollTo(0, 0);
    
    const response = await fetch(API_URL, {   
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": CSRF_TOKEN,
        },
        body: JSON.stringify({
            "curr_input" : message,
            "conversation_id": window.conversation_id, 
        })
    })
    console.log('Connected API');
    
    const text = await response.json();
    console.log(text)
    document.getElementById(`gpt_${window.token}`).innerHTML = markdown.render(text);

    window.scrollTo(0, 0);
    await add_message(window.conversation_id, "user", message);
    await add_message(window.conversation_id, "assistant", text);
};


const message_input = document.getElementById(`message-input`);
const handle_ask = async () => {
	message_input.style.height = `80px`;
	message_input.focus();

	window.scrollTo(0, 0);
	let message = message_input.value;

	if (message.length > 0) {
		message_input.value = ``;
		await ask_gpt(message);
	}
};

const send_button = document.querySelector(`#send-button`);
window.onload = async () => {
    await load_conversations();
	send_button.addEventListener(`click`, async () => {
		console.log("clicked send");
		await handle_ask();
	});
}