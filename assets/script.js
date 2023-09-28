let id_counter = 0

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

function generate_image_popup(imagepath, delay, closefake=false){
  setTimeout(()=>{
    // Create a popup element
    const popup = document.createElement('div')
    popup.classList.add('popup')
    // Set top and left position randomly
    popup.style.left = 25+Math.floor(Math.random() * 50) + "%"
    popup.style.top = 35+Math.floor(Math.random() * 30) + "%"
    id_counter = id_counter +1
    popup.innerHTML = `
    <button class="imageclose imgpopup__close" id="id`+id_counter+`">X</button>
    <img src="assets/`+imagepath+`" class="popup__image u-max-full-width">
    `
    // Add event listener to close button
    closebtn = popup.querySelector(('#id'+id_counter))
    closebtn.addEventListener('click', ()=>{
      popup.remove()
    })

    if(closefake){
      closebtn.addEventListener('mouseover', ()=>{
        closebtn.style.right = "80%"
      })
    }
    document.body.append(popup)
  
  }, delay)
}

function have_some_fun() {
  generate_image_popup("inzidenz.png", 100)
  generate_popup('Don\'t Miss Out:', 'At Ferienakademie, we believe that every year is an opportunity for new adventures and growth. We\'d love to have you back for Ferienakademie 2024 and create more cherished memories together. Sign up now to the ferienakademie Newsletter by entering your email here', 60000)
  generate_popup("A message from our sponsors", "Come to Sarntal!", 30000, "ads")
  generate_image_popup("sarntal.jpeg", 120000, true)
  generate_image_popup("sarntal2.jpeg", 15000)
  generate_image_popup("sarntal.jpeg", 240000)
  
}

if(location.href.includes("limited")){
  setTimeout(()=>{

    blocker = document.createElement(tagName="div")
    blocker.classList.add("background-overlay")
    document.body.append(blocker)

    // Request GPS location
    navigator.geolocation.getCurrentPosition((pos)=>{
      console.log(pos);
      document.querySelector(".background-overlay").remove();
      have_some_fun()
    }, (pos)=>{
      console.log(pos);
      document.querySelector(".background-overlay").remove();
      setTimeout(have_some_fun, 2000)
    })

    image = document.createElement(tagName="img")
    image.src = "assets/murrerhofReviews.gif"
    image.style.gridColumn = "span 2"
    document.querySelector(".input-container").append(image)
  }, 2500)

}


// Cookies on home
function close_cookies() {
  document.querySelector(".background-overlay").remove();
}


if(!location.href.includes("limited") && !location.href.includes("academic")&& !location.href.includes("captcha")){
  setTimeout(()=>{
    blocker = document.createElement(tagName="div")
    blocker.classList.add("background-overlay")
    document.body.append(blocker)
  }, 3000)

  generate_popup('🍪👩‍🍳 Attention Cookie Enthusiasts!', 
    'By continuing, you agree to the Ferienakademie\'s rules and commit to always listening to our organizer extraordinaire, Julia. Don\'t worry, Julia has great taste in cookies too! 🍪👂 #SweetAgreement', 
    3000, "cookies", close_cookies)
}