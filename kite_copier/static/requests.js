const get_data = async (url, keys) => {
  const response = await fetch(url+keys); // Generate the Response object
  if (response.ok) {
    const jsonValue = await response.json(); // Get JSON value from the response body
    return Promise.resolve(jsonValue);
  } else {
    return Promise.reject("not found");
  }
};

  const buildLtpUrl = () => {
   const token = document.getElementById('token')
   const symbol = document.getElementById('symbol')
   const exchange = document.getElementById('exchange')
    let key = '?symbol=';
  if (symbol.value.length > 0) {
    key += symbol.value; }
  else { return "" }
  if (token.value.length > 0) {
    key = key + '&token=' + token.value; }
  else { return "" }
  if (exchange.value.length > 0) {
    key = key + '&exchange=' + exchange.value; 
    return key
  }
  else { return ""}
}



