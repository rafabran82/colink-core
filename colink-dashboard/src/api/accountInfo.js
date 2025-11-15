export async function fetchAccountInfo() {
  const response = await fetch("http://localhost:5000/get-account-info");

  if (!response.ok) {
    throw new Error(`Failed to fetch account info: ${response.status} ${response.statusText}`);
  }

  const text = await response.text();

  const getMatch = (regex) => {
    const m = text.match(regex);
    return m ? m[1] : null;
  };

  const info = {
    raw: text,
    Account: getMatch(/Account:\s*'([^']+)'/),
    Balance: getMatch(/Balance:\s*'([^']+)'/),
    Flags: getMatch(/Flags:\s*(\d+)/),
    OwnerCount: getMatch(/OwnerCount:\s*(\d+)/),
    LedgerEntryType: getMatch(/LedgerEntryType:\s*'([^']+)'/)
  };

  return info;
}
