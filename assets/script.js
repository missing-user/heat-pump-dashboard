function generate_popup(title, text, delay, elementtype="newsletter", callback=undefined){
  setTimeout(()=>{
    // Create a popup element
    const popup = document.createElement('div')
    popup.classList.add(elementtype)
    popup.classList.add('popup')
    popup.style.left = 25+Math.floor(Math.random() * 50) + "%"
    popup.style.bottom = 35+Math.floor(Math.random() * 30) + "%"

    popup.innerHTML = `
    <h2 class="popup__title">`+title+`</h2>
    <p class="popup__text">`+text+`</p>
    <button class="popup__close">`+(elementtype=="cookies"?"Accept":"Close")+`</button>
    `
    // Add event listener to close button
    popup.querySelector('.popup__close').addEventListener('click', ()=>{
      if(callback)
        callback()
      popup.remove();
    })
    document.body.append(popup)
  
  }, delay)
}

function generate_image_popup(imagepath, delay, closefake=true){
  setTimeout(()=>{
    // Create a popup element
    const popup = document.createElement('div')
    popup.classList.add('popup')
    // Set top and left position randomly
    popup.style.left = 25+Math.floor(Math.random() * 50) + "%"
    popup.style.top = 35+Math.floor(Math.random() * 30) + "%"

    popup.innerHTML = `
    <button class="imageclose imgpopup__close">X</button>
    <img src="assets/`+imagepath+`" class="popup__image">
    `
    // Add event listener to close button
    closebtn = popup.querySelector('.imgpopup__close')
    closebtn.addEventListener('click', ()=>{
      popup.remove()
    })

    if(closefake){
      closebtn.addEventListener('mouseover', ()=>{
        closebtn.disabled = true
        closebtn.style.right = "80%"
        setTimeout(()=>{closebtn.disabled = false;}, 300)
      })
    }
    document.body.append(popup)
  
  }, delay)
}

function have_some_fun() {
  setTimeout(handler=()=>{
    //request push notification permission
    Notification.requestPermission().then((result)=>{
      console.log(result)
    })
  }, 500)
  
  document.querySelector(".background-overlay").remove();

  generate_popup('Would you like to learn more about heat pumps?', 'Sign up for our newsletter to stay up to date with the latest news!', 6000)
  generate_popup("A message from our sponsors", "Come to Sarntaal!", 3000, "ads")
  generate_image_popup("inzidenz.png", 100)
}

if(location.href.includes("limited")){
  let cookieDelay = 3000
  setTimeout(()=>{
    blocker = document.createElement(tagName="div")
    blocker.classList.add("background-overlay")
    document.body.append(blocker)

    // Request GPS location
    navigator.geolocation.getCurrentPosition((pos)=>{
      console.log(pos)
    })
  }, cookieDelay)
  generate_popup('Psst - Here\'s some cookies...', 
    'Please accept our innocent little tracking cookies, they\'re nice and yummy', 
    cookieDelay, "cookies", have_some_fun)
}