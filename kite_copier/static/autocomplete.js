// Function to do an Ajax call
let prevSearch = "";
const exchange = document.getElementById("exchange");
const token = document.getElementById("token");
const price = document.getElementById("price");
const trigger = document.getElementById("trigger");
const lotsize = document.getElementById("lotsize");
const ac_input = document.getElementById("symbol");

// General function to update quantities based on the current lot size and multipliers.
function updateQuantities() {
  const lotSize = parseInt(lotsize.value) || 0;

  document.querySelectorAll("tr").forEach((row) => {
    const qtyInput = row.querySelector('input[name="qty"]');
    const multiplierInput = row.querySelector('input[name="multiplier"]');

    if (qtyInput && multiplierInput) {
      const multiplier = parseInt(multiplierInput.value) || 1;
      qtyInput.value = lotSize * multiplier; // Update qty based on lotSize * multiplier
    }
  });
}

// Attach an event listener to update quantities when `lotsize` is manually changed.
lotsize.addEventListener("input", updateQuantities);

/*******************************************

// main autocomplete function

//******************************************/
const autocomplete = (inp) => {
  let currentFocus;
  /*the autocomplete function takes two arguments,
  the text field element and an array of possible autocompleted values:*/
  /*execute a function when someone writes in the text field:*/
  inp.addEventListener("input", function () {
    const val = this.value.toUpperCase();
    /*close any already open lists of autocompleted values*/
    closeAllLists();
    if (!val || val.length <= 2 || val == prevSearch) {
      return false;
    } else {
      prevSearch = val;
    }
    currentFocus = -1;
    /*create cntr DIV element that will contain the items (values):*/
    const cntr = document.createElement("DIV");
    cntr.setAttribute("id", this.id + "autocomplete-list");
    cntr.setAttribute("class", "autocomplete-items");
    cntr.addEventListener("click", (e) => {
      atr = e.target.getAttribute("auto-item");
      if (atr) {
        // Insert the values from the autocomplete.
        data = e.target.dataset;
        exchange.value = data.exchange;
        lotsize.value = data.lot;
        // Symbol
        inp.value = data.symbol;

        // Call updateQuantities here after setting lotsize from autocomplete
        updateQuantities();
        // Close the list.
        closeAllLists();
      } else {
        console.log(e.target, e.target.tagName);
      }
    });
    /*append the DIV element as a child of the autocomplete container:*/
    this.parentNode.appendChild(cntr);
    get_data("/search?sym=", val).then((arr) => {
      for (let i = 0; i < arr.length; i++) {
        dobj = arr[i];
        sym = dobj.tradingsymbol;
        /*check if the item starts with the same letters as the text field value:*/
        // if (arr[i][1].substr(0, val.length).toUpperCase() == val.toUpperCase()) {
        if (sym) {
          /*create a DIV element for each matching element:*/
          const list = document.createElement("DIV");
          list.setAttribute("auto-item", true);
          // list.classList.add('badge')
          list.dataset.symbol = sym;
          list.dataset.exchange = dobj.exchange;
          list.dataset.lot = dobj.lot_size;
          // list.innerHTML += dobj.instrument_type
          let index = sym.search(val);
          if (index > 0) {
            list.innerHTML += sym.substr(0, index);
          }
          list.innerHTML +=
            "<strong>" + sym.substr(index, val.length) + "</strong>";
          list.innerHTML += sym.substr(index + val.length);
          cntr.appendChild(list);
        } // end of if
      } // end of for
    }); // end of get_data
  }); // end of input even listener

  /*execute a function presses a key on the keyboard:*/
  inp.addEventListener("keydown", function (e) {
    let x = document.getElementById(this.id + "autocomplete-list");
    if (x) x = x.getElementsByTagName("div");
    if (e.keyCode == 40) {
      /*If the arrow DOWN key is pressed,
      increase the currentFocus variable:*/
      currentFocus++;
      /*and and make the current item more visible:*/
      addActive(x);
    } else if (e.keyCode == 38) {
      //up
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

  function addActive(x) {
    /*a function to classify an item as "active":*/
    if (!x) return false;
    /*start by removing the "active" class on all items:*/
    removeActive(x);
    if (currentFocus >= x.length) currentFocus = 0;
    if (currentFocus < 0) currentFocus = x.length - 1;
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
};
/*******************************/
// end of autocomplete
/******************************/
autocomplete(ac_input);
