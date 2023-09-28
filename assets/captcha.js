const cellOptions = [
  {
    classification: "meat",
    imgSrc:
      "assets/PXL_20230928_061638611.jpg"
  },
  {
    classification: "meat",
    imgSrc:
      "assets/WhatsApp Image 2023-09-28 at 08.10.57.jpeg"
  },
  {
    classification: "veg",
    imgSrc:
      "assets/buckethat.png"
  },
  {
    classification: "meat",
    imgSrc:
      "assets/IMG_6356.png"
  },
  {
    classification: "meat",
    imgSrc:
      "assets/IMG_6344.png"
  },
  {
    classification: "meat",
    imgSrc:
      "assets/IMG_6355.png"
  },
  {
    classification: "veg",
    imgSrc:
      "assets/IMG_6348.png"
  },
  {
    classification: "veg",
    imgSrc:
      "assets/IMG_6364.png"
  },
  {
    classification: "meat",
    imgSrc:
      "assets/IMG_6365.png"
  }
];

function shuffle(array) {
  let currentIndex = array.length,
    randomIndex;
  while (currentIndex != 0) {
    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex--;
    [array[currentIndex], array[randomIndex]] = [
      array[randomIndex],
      array[currentIndex]
    ];
  }
  return array;
}

let shuffledOptions = [];
let humanPercent = 10;

function createCaptcha() {
  shuffledOptions = shuffle(cellOptions);

  // Create html from raw string
let captchaHtml = `
<div class="background-overlay"></div>
<div class="captcha-wrap">
  <div class="captcha-title">
    <p class="captcha-title__subtitle">
      <small class="captcha-title__greeting">We need to verify your humanity...</small>
      <h5 class="captcha-title__version-info">Ferienakademie Captcha v 2.0</h5>
    </p>
    <h3 class="captcha-title__command">Select All Vegetarians</h3>
  </div>
  <div class="captcha">
  </div>
  <div class="captcha-actions">
    <button type="button" id="cbtn-submit" class="btn-submit">Submit</button>
  </div>  
</div>`
  const captchaw = document.createElement("div")
  captchaw.innerHTML = captchaHtml;
  captchaw.style.display = "flex"
  captchaw.style.position = "absolute"
  captchaw.style.top = "20%"
  captchaw.style.left = "45%"
  document.body.append(captchaw);
  const captcha = captchaw.querySelector(".captcha");

  let innerHTML = "";
  for (var option of shuffledOptions) {
    innerHTML += `
  <div class="captcha-cell" data-classification="${option.classification}">
    <img src="${option.imgSrc}"  />
  </div>
  `;
  }

  captcha.innerHTML = innerHTML;

  Array.from(document.querySelectorAll(".captcha-cell")).forEach((el) => {
    el.addEventListener("click", () => {
      el.classList.toggle("selected");
    });
  });



const submitButton = document.querySelector("#cbtn-submit");
submitButton.addEventListener("click", () => {
  const numberOfVegs = shuffledOptions.filter(
    (opt) => opt.classification == "veg"
  ).length;
  const selectedElements = Array.from(
    document.querySelectorAll(".captcha-cell.selected")
  );

  const countMismatch = numberOfVegs != selectedElements.length;
  const invalidSelections = selectedElements.filter(
    (opt) => opt.dataset.classification != "veg"
  );

  if (invalidSelections.length || countMismatch) {
    console.log("error");
    document.querySelector(".captcha-wrap").classList.add("error");
  } else {
    console.log("succeed");
    document.querySelector(".captcha-wrap").classList.remove("error");
    document.querySelector(".background-overlay").remove();
    document.querySelector(".captcha-wrap").remove();

    // Navigate to the next page
    window.location.href = "http://127.0.0.1:8050/limited";
  }
});

}


if(location.href.includes("captcha")){
  createCaptcha()
}