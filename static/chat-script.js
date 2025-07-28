//Chat
let receiverID = document.getElementById("ReceiverId");
let friends = {
    list: document.querySelector('.chat-left .people'),
    all: document.querySelectorAll('.chat-left .people .people-chat'),
    name: '',
    user: [],
    right: ''
},
    chat = {
        container: document.querySelector('.chat-right'),
        current: null,
        person: null,
        name: document.querySelector('.chat-right .header .name'),
        dataChat: document.querySelector('.chat-right .chats')
    }

friends.all.forEach(f => {
    f.addEventListener('mousedown', () => {
        f.classList.contains('active') || setAciveChat(f)
    })
});

function setAciveChat(f) {
    let activeList = friends.list.querySelector('.active');
    if (activeList) {
        activeList.classList.remove('active');
    }
    f.classList.add('active')
    chat.current = chat.container.querySelector('.active-chat')
    chat.person = f.getAttribute('data-chat')
    if (chat.current) {
        chat.current.classList.remove('active-chat')
    }
    //header toggle
    chat.user = f.getAttribute('data-user').split("~");
    let header = chat.container.querySelector('.header')
    header.style.display = "block";
    chat.right = chat.container.querySelector('.prof-img');
    const imag = chat.container.querySelector('.prof-img img');
    const status = chat.container.querySelector('.status');
    if (chat.user[0]) {
        imag.src = '/' + chat.user[0];
    }
    sessionStorage.setItem("imageRef", chat.user[0])
    sessionStorage.setItem("isLoggedIn", chat.user[1].toLowerCase())

    if (chat.user[1].toLowerCase() === "true") {
        chat.right.classList.add("online");
        status.innerHTML = "Online";
    }
    else {
        const online = chat.container.querySelector(".prof-img.online");
        if (online) {
            chat.right.classList.remove("online");
        }
        status.innerHTML = "Offline";
    }
    //----

    receiverID.value = chat.person;
    friends.name = f.querySelector('.name').innerText
    chat.name.innerHTML = friends.name
    let chatActive = chat.container.querySelector('[data-chat="' + chat.person + '"]');
    chatActive.classList.add('active-chat');

    sessionStorage.setItem("activeId", chat.person);
}
//session storage
const activedId = sessionStorage.getItem("activeId");
if (activedId && receiverID) {
    receiverID.value = `${activedId}`;
    //header
    let header = chat.container.querySelector('.header')
    header.style.display = "block";
    chat.right = chat.container.querySelector('.prof-img');
    const imag = chat.container.querySelector('.prof-img img');
    const status = chat.container.querySelector('.status');

    const imageRef = sessionStorage.getItem("imageRef");
    const isLoggedIn = sessionStorage.getItem("isLoggedIn");

    if (imageRef) {
        imag.src = '/' + imageRef;
    }
    if (isLoggedIn === "true") {
        chat.right.classList.add("online");
        status.innerHTML = "Online";
    }
    else {
        const online = chat.container.querySelector(".prof-img.online");
        if (online) {
            chat.right.classList.remove("online");
        }
        status.innerHTML = "Offline";
    }
    //end header

    chat.current = chat.container.querySelector('.active-chat')
    if (chat.current) {
        chat.current.classList.remove('active-chat')
    }
    let chatActive = chat.container.querySelector('[data-chat="' + activedId + '"]');
    chatActive.classList.add('active-chat');

    let activeList = friends.list.querySelector('.active');
    if (activeList) {
        activeList.classList.remove('active');
    }

    let leftActive = friends.list.querySelector('[data-chat="' + activedId + '"]');
    leftActive.classList.add('active');
    friends.name = leftActive.querySelector('.name').innerText
    chat.name.innerHTML = friends.name
}



//tab active
const tabButton = document.querySelectorAll(".nav-tabs .nav-link");
const tabButtonActive = document.querySelector(".nav-tabs .nav-link.active");
if (tabButton) {
    tabButton.forEach(t => {
        t.addEventListener("click", () => {
            sessionStorage.setItem("activeNavTabId", t.getAttribute("id"));
        })
    })
}

//active Session Storage
const activeNavId = sessionStorage.getItem("activeNavTabId");
const tabContent = document.querySelector(".tab-pane.show.active");
if (activeNavId) {
    if (tabButtonActive) {
        tabButtonActive.classList.remove("active");
        tabContent.classList.remove("show", "active");
    }
    const tabActive = document.getElementById(activeNavId);
    const tabCont = document.querySelector("[aria-labelledby='" + activeNavId + "']");
    tabActive.classList.add("active");
    tabCont.classList.add("show","active")
}
