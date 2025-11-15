export async function fetchAccountBalance() {
  const response = await fetch("http://localhost:5000/get-account-balance");

  if (!response.ok) {
    throw new Error(`Failed to fetch account balance: ${response.status} ${response.statusText}`);
  }

  const text = await response.text();
  const value = Number(text);

  if (Number.isNaN(value)) {
    console.warn("Account balance response is not a number:", text);
    return text;
  }

  return value;
}
