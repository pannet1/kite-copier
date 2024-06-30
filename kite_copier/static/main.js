const debugScript = false;

const sync_frm_clr = (bors) => {
  const frm = document.getElementById('frm')
  if (bors=='BUY') {
    frm.classList.remove('bg-red-300');
    frm.classList.add('bg-green-500');
  } else {
    frm.classList.add('bg-red-300');
    frm.classList.remove('bg-green-500');
  }
}

const tblColCnt = (tableId, colNumber, ttlTagName) =>
  {
  let result = 0;
  try
  {
    const tableElem = window.document.getElementById(tableId); 		   
    const tableBody = tableElem.getElementsByTagName("tbody").item(0);
    const howManyRows = tableBody.rows.length;
    for (let i=0; i<(howManyRows); i++) // skip first and last row (hence i=1, and howManyRows-1)
    {
       let thisTrElem = tableBody.rows[i];
       let thisTdElem = thisTrElem.cells[colNumber];			
       let thisTextNode = thisTdElem.childNodes.item(0);
       let thisNumber = parseFloat(thisTextNode.data);
       if (!isNaN(thisNumber)) 
         result += thisNumber;       

	  } // end for

  } // end try
  catch (ex)
  {
     console.log("Exception in function tblColCnt()\n" + ex);
  }
  finally
  {
     const elemTtl = window.document.getElementById(ttlTagName);
     elemTtl.innerHTML = parseInt(result);
  }
}



