// Function to do an Ajax call
let prevSearch = ""
const exchange = document.getElementById('exchange');
const token = document.getElementById('token');
const price = document.getElementById('price');
const trigger = document.getElementById('trigger');
const lotsize = document.getElementById('lotsize');
const ac_input = document.getElementById("symbol");

/*******************************************

// main autocomplete function

//******************************************/
const autocomplete = (inp) => {
let currentFocus;
  /*the autocomplete function takes two arguments,
  the text field element and an array of possible autocompleted values:*/
  /*execute a function when someone writes in the text field:*/
  inp.addEventListener("input", function(e) {
    const val = this.value;
    /*close any already open lists of autocompleted values*/
    closeAllLists();
    if (!val || (val.length <=2) || val == prevSearch)
    { return false;}
    else { prevSearch = val}
    currentFocus = -1;
    /*create cntr DIV element that will contain the items (values):*/
    const cntr = document.createElement("DIV");
    cntr.setAttribute("id", this.id + "autocomplete-list");
    cntr.setAttribute("class", "autocomplete-items");
    /*append the DIV element as a child of the autocomplete container:*/
    this.parentNode.appendChild(cntr);
    get_data('/mw/', val).then(arr => {
      for (let i=0; i< arr.length; i++) {
        /*check if the item starts with the same letters as the text field value:*/
        if (arr[i][1].substr(0, val.length).toUpperCase() == val.toUpperCase()) {
          /*create a DIV element for each matching element:*/
          const list = document.createElement("DIV");
          list.innerHTML = "<strong>" + arr[i][1].substr(0, val.length) + "</strong>";
          list.innerHTML += arr[i][1].substr(val.length);
          list.innerHTML += "<input name='token' type='hidden' value='" + arr[i][1] + "'>";
          /*execute a function when someone clicks on the item value (DIV element):*/
          list.addEventListener("click", function(e) {
          exchange.value = arr[i][3]
          lotsize.textContent = arr[i][2]
          /*insert the value for the autocomplete text field:*/
          inp.value = this.getElementsByTagName("input")[0].value;
          token.value = arr[i][0]
          closeAllLists();
          const key = buildLtpUrl()
          if (key.length > 0) {
            get_data('/ltp/', key).then(data => {
              price.value = data[0][0];
              trigger.value = 0
            });
          }

          });
          cntr.appendChild(list);
        } // end of if
      } // end of for
    });  // end of get_data

    /*execute a function presses a key on the keyboard:*/
    inp.addEventListener("keydown", function(e) {
      let x = document.getElementById(this.id + "autocomplete-list");
      if (x) x = x.getElementsByTagName("div");
      if (e.keyCode == 40) {
        /*If the arrow DOWN key is pressed,
        increase the currentFocus variable:*/
        currentFocus++;
        /*and and make the current item more visible:*/
        addActive(x);
      } else if (e.keyCode == 38) { //up
        /*If the arrow UP key is pressed,
        decrease the currentFocus variable:*/
        currentFocus--;
        /*and and make the current item more visible:*/
        addActive(x);
      } else if (e.keyCode == 13) {
        /*If the ENTER key is pressed, prevent the form from being submitted,*/
        e.preventDefault();
        if (currentFocus > -1) {
          /*and simulate a click on the "active" item:*/
          if (x) x[currentFocus].click();
        }
      }
    }); // end of keydown event listener
  }); // end of input even listener

  function addActive(x) {
    /*a function to classify an item as "active":*/
    if (!x) return false;
    /*start by removing the "active" class on all items:*/
    removeActive(x);
    if (currentFocus >= x.length) currentFocus = 0;
    if (currentFocus < 0) currentFocus = (x.length - 1);
    /*add class "autocomplete-active":*/
    x[currentFocus].classList.add("autocomplete-active");
  }

  function removeActive(x) {
    /*a function to remove the "active" class from all autocomplete items:*/
    for (let i = 0; i < x.length; i++) {
      x[i].classList.remove("autocomplete-active");
    }
  }

  function closeAllLists(elmnt) {
    /*close all autocomplete lists in the document,
    except the one passed as an argument:*/
    const x = document.getElementsByClassName("autocomplete-items");
    for (let i = 0; i < x.length; i++) {
      if (elmnt != x[i] && elmnt != inp) {
      x[i].parentNode.removeChild(x[i]);
      }
    }
  }

  /*execute a function when someone clicks in the document:*/
  document.addEventListener("click", function (e) {
      closeAllLists(e.target);
  });
}
/*******************************/
// end of autocomplete
/******************************/
autocomplete(ac_input)
// Init a timeout variable to be used below
// Listen for keystroke events

/*
let timeout = null;
ac_input.addEventListener('keyup', function (e) {
  // Clear the timeout if it has already been set.
  // This will prevent the previous task from executing
  // if it has been less than <MILLISECONDS>
  clearTimeout(timeout);
  // Make a new timeout set to go off in 1000ms (1 second)
  timeout = setTimeout(function () {
    console.log("timeout")
  }, 1000);
})
*/
