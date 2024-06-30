// consumes sync_frm_clr from main.js
document.addEventListener('DOMContentLoaded', () => {
  const txn = document.getElementById('txn')
  txn.checked = true
  txn.onclick = function() {
    if (txn.checked == true) {
      sync_frm_clr('BUY')
    } else {
      sync_frm_clr('SELL')
    }
  }
  if (txn.checked == true)
    sync_frm_clr('BUY')
});

const copyButton = document.getElementById('copyButton');
copyButton.addEventListener('click', () => {
  // unhide the button class 
  const btn_basket = document.getElementById('btn_basket');
  const sourceTable = document.querySelector('.mx-auto.table.table-compact');
  const targetTable = document.getElementById('basket_table');
  const rowsToCopy = Array.from(sourceTable.querySelectorAll('tr')).filter((row) => {
    const qtyInput = row.querySelector('input[name="qty"]');
    return qtyInput && Number(qtyInput.value) > 0;
  });

  rowsToCopy.forEach((row, index) => {
    const newRow = document.createElement('div');
    newRow.classList.add('stat', 'place-items-center');

    const txnCheckbox = document.getElementById('txn');
    const txnValue = txnCheckbox.checked ? 'BUY' : 'SELL';
    const txnInputField = document.createElement('input');
    txnInputField.name = 'transactiontype';
    txnInputField.value = txnValue;
    txnInputField.type = 'hidden';
    newRow.appendChild(txnInputField);

    const symbolInput = document.getElementById('symbol');
    const symbolInputField = document.createElement('input');
    symbolInputField.name = 'tradingsymbol';
    symbolInputField.value = symbolInput.value;
    symbolInputField.type = 'hidden'
    newRow.appendChild(symbolInputField);


    const clientNameInput = row.querySelector('input[name="client_name"]');
    const clientName = clientNameInput.value;
    const clientNameInputField = document.createElement('input');
    clientNameInputField.name = 'client_name';
    clientNameInputField.value = clientName;
    clientNameInputField.type = 'hidden';
    newRow.appendChild(clientNameInputField);

    const priceInput = document.getElementById('price');
    const priceInputField = document.createElement('input');
    priceInputField.name = 'price';
    priceInputField.value = priceInput.value;
    priceInputField.type = 'hidden';
    newRow.appendChild(priceInputField);

    let ptype;
    const ptypeInputs = Array.from(document.querySelectorAll('input[name="ptype"]'));
    ptypeInputs.forEach((input) => {
      if (input.checked) {
        const title = input.getAttribute('data-title');
        if (title == "NRML") {
          ptype = 'CARRYFORWARD'
        } else if (title == "MIS") {
          ptype = 'INTRADAY'
        } else {
          ptype = 'DELIVERY'
        }
        const ptypeInput = document.createElement('input');
        ptypeInput.name = 'ptype';
        ptypeInput.value = ptype;
        ptypeInput.type = 'hidden';
        newRow.appendChild(ptypeInput);
      }
    });

    const qtyInput = row.querySelector('input[name="qty"]');
    const qty = qtyInput.value;
    const qtyInputField = document.createElement('input');
    qtyInputField.name = 'quantity';
    qtyInputField.value = qty;
    qtyInputField.type = 'hidden';
    newRow.appendChild(qtyInputField);

    const triggerInput = document.getElementById('trigger');
    const triggerInputField = document.createElement('input');
    triggerInputField.name = 'trigger';
    triggerInputField.value = triggerInput.value;
    triggerInputField.type = 'hidden';
    newRow.appendChild(triggerInputField);

    let otype;
    const otypeInputs = Array.from(document.querySelectorAll('input[name="otype"]'));
    otypeInputs.forEach((input) => {
      if (input.checked) {
        const title = input.getAttribute('data-title');
        if (title == "LMT") {
          otype = "LIMIT"
        } else if (title == "MKT") {
          otype = "MARKET"
        } else if (title == "SL") {
          otype = "STOPLOSS_LIMIT"
        } else {
          otype = "STOPLOSS_MARKET"
        }
        const otypeInput = document.createElement('input');
        otypeInput.name = 'otype';
        otypeInput.value = otype;
        otypeInput.type = 'hidden';
        newRow.appendChild(otypeInput);
      }
    });

    const exchInput = document.getElementById('exchange');
    const exchInputField = document.createElement('input');
    exchInputField.name = 'exchange';
    exchInputField.type = 'hidden';
    exchInputField.value = exchInput.value;
    newRow.appendChild(exchInputField);

    const tknInput = document.getElementById('token');
    const tknInputField = document.createElement('input');
    tknInputField.name = 'token';
    tknInputField.type = 'hidden';
    tknInputField.value = tknInput.value;
    newRow.appendChild(tknInputField);

    /* css styling and beautification */

    const statTitleDiv = document.createElement('div');
    statTitleDiv.textContent = priceInput.value + " / " + triggerInput.value

    const statValueDiv = document.createElement('div');
    statValueDiv.className = 'stat-value';

    const statDescDiv = document.createElement('div');
    statDescDiv.textContent = clientNameInput.value + " / " + otype + " / " + ptype

    if (txnInputField.value == 'SELL') {
      statTitleDiv.className = 'stat-title text-red-500';
      newRow.appendChild(statTitleDiv)

      statValueDiv.textContent = "-" + qtyInput.value + " " + symbolInputField.value;
      newRow.appendChild(statValueDiv);

      statDescDiv.className = 'stat-desc text-red-500';
      newRow.appendChild(statDescDiv)
    } else {
      statTitleDiv.className = 'stat-title text-green-500';
      newRow.appendChild(statTitleDiv)

      statValueDiv.textContent = qtyInput.value + " " + symbolInputField.value;
      newRow.appendChild(statValueDiv);

      statDescDiv.className = 'stat-desc text-green-500';
      newRow.appendChild(statDescDiv)

    }
    /* end of css beautification */

    targetTable.appendChild(newRow);
  });

  btn_basket.classList.remove('hidden');
});
