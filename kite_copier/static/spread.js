// enables disables status of Quantsapp
function toggleStatus(spreadId, currentStatus) {
  const newStatus = currentStatus === 0 ? 1 : 0;
  fetch(`/toggle_status?id=${spreadId}&status=${newStatus}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })
    .then(response => response.json())
    .then(data => {
      console.log(data);
    })
    .catch(error => {
      console.error('Error:', error);
    });
}

// toggles itemsRow visiblity
function toggleItems(spreadId) {
  const itemsRow = document.getElementById(`items-row-${spreadId}`);
  if (itemsRow.style.display === "none") {
    itemsRow.style.display = "table-row";
  } else {
    itemsRow.style.display = "none";
  }
}

/*
 *
 *  Create Item modal functions
 *
 */
const addFormButtons = document.querySelectorAll(".add-form-button");
const userDropdown = document.getElementById("userDropdown");
const sellCheckbox = document.getElementById("sellCheckbox");
const symbolDropdown = document.getElementById("symbolDropdown");
const entryInput = document.getElementById("entry");
const qtyInput = document.getElementById("qty");
const tokenHidden = document.getElementById("tokenId");
const exchangeHidden = document.getElementById("exchangeId");
const ltpHidden = document.getElementById("ltpId");
let apiData = []; // Initialize an empty array to store API data

// Event listeners 
userDropdown.addEventListener("change", updateSymbolDropdown);
sellCheckbox.addEventListener("change", updateSymbolDropdown);

/**
  *
  * not used 
  *
addFormButtons.forEach(button => {
  button.addEventListener("click", async (event) => {
    const selectedUser = button.getAttribute("data-user");
    const selectedSymbol = button.getAttribute("data-symbol");
    const formRow = document.createElement("tr");
    formRow.innerHTML = `
              <td colspan="4">
                  <form action="/submit_position" method="POST">
                      <input type="hidden" name="user" value="${selectedUser}">
                      <input type="hidden" name="symbol" value="${selectedSymbol}">
                      <input type="submit" value="Submit">
                  </form>
              </td>
          `;
    const parentRow = button.parentNode.parentNode;
    parentRow.parentNode.insertBefore(formRow, parentRow.nextSibling);
  });
});

*/

// passes the spreadId to the new item before creating
const hiddenSpreadId = document.getElementById("receiveSpreadId");
function sendSpreadId(spreadId = 0) {
  hiddenSpreadId.value = spreadId;
}

const hiddenSpreadIdForUsers = document.getElementById("receiveSpreadIdForUsers")
function sendSpreadIdForUsers(spreadId = 0) {
  hiddenSpreadIdForUsers.value = spreadId;
}

// user badge closeable
const closeButtons = document.querySelectorAll(".close-badge");
closeButtons.forEach(button => {
  button.addEventListener("click", event => {
    const badge = event.target.closest(".badge");
    if (badge) {
      badge.remove(); // Remove the clicked badge
    }
  });
});

// Function to fetch data from the FastAPI endpoint
async function fetchDataFromAPI(userId, transactionType) {
  const response = await fetch(`/positionbook?user_id=${userId}&txn_type=${transactionType}`);
  const data = await response.json();
  return data;
}

// Function to update the symbol dropdown based on selections
async function updateSymbolDropdown() {
  const selectedOption = userDropdown.options[userDropdown.selectedIndex];
  const selectedUserId = selectedOption.getAttribute("id");
  const transactionType = sellCheckbox.checked ? "Buy" : "Sell";
  symbolDropdown.addEventListener("change", function() {
    const selectedSymbol = symbolDropdown.value;
    updateEntryQtyInputs(selectedSymbol);
  });
  if (selectedUserId) {
    apiData = await fetchDataFromAPI(selectedUserId, transactionType);
    symbolDropdown.innerHTML = "<option disabled selected>Select Symbol</option>";
    apiData.forEach(symbol => {
      const option = document.createElement("option");
      option.value = symbol.tradingsymbol; // Using the tradingsymbol key from the JSON response
      option.textContent = symbol.tradingsymbol; // Using the tradingsymbol key from the JSON response
      symbolDropdown.appendChild(option);
    });
  }
}

function updateEntryQtyInputs(selectedSymbol) {
  const selectedSymbolData = apiData.find(symbol => symbol.tradingsymbol === selectedSymbol);
  if (selectedSymbolData) {
    // Update values
    entryInput.value = selectedSymbolData.avgnetprice;
    qtyInput.value = Math.abs(selectedSymbolData.netqty);
    tokenHidden.value = selectedSymbolData.symboltoken;
    exchangeHidden.value = selectedSymbolData.exchange;
    ltpHidden.value = selectedSymbolData.ltp;
  } else {
    tokenHidden.value = '';
    exchangeHidden.value = '';
  }
}

