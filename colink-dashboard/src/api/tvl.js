export async function fetchXRPLTVL() {
    try {
        const res = await fetch("http://localhost:5000/api/xrpl/tvl");
        return await res.json();
    } catch (err) {
        console.error("TVL fetch error:", err);
        return { error: "Failed to fetch XRPL TVL" };
    }
}
