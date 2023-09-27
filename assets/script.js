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
  generate_popup('Would you like to learn more about heat pumps?', 'Sign up for our newsletter to stay up to date with the latest news!', 6000)
  generate_popup("A message from our sponsors", "Come to Sarntaal!", 3000, "ads")
  generate_image_popup("inzidenz.png", 100)

}

if(location.href.includes("limited")){
  generate_popup('Psst - Here\'s some cookies...', 'Please accept our innocent little tracking cookies, they\'re nice and yummy', 1300, "cookies", have_some_fun)


}