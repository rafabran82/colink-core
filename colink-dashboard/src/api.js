// Deprecated API shim — dashboard now uses src/api/pools.ts
// These remain only to prevent import crashes before full migration.

export async function fetchPoolState() {
  return null;
}

export async function fetchSwapLogs() {
  return [];
}

export async function fetchSimMeta() {
  return null;
}
