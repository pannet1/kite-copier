// consumes sync_frm_clr from main.js
document.addEventListener('DOMContentLoaded', () => {
  const txn = document.getElementById('txn')
  txn.checked = true
  txn.onclick = function () {
    if (txn.checked == true) {
      sync_frm_clr('BUY')
    } else {
      sync_frm_clr('SELL')
    }
  }
  if (txn.checked == true)
    sync_frm_clr('BUY')
});

