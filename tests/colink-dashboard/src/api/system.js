/**
 * COLINK Dashboard System API Client
 *
 * Provides calls to backend endpoints:
 *  - /health
 *  - /version
 *  - /config
 *  - /status
 */

const BASE_URL = "http://localhost:5000"; // Dashboard backend proxy target

async function apiGet(path) {
    try {
        const res = await fetch(`${BASE_URL}${path}`);
        if (!res.ok) {
            throw new Error(`API error ${res.status}: ${path}`);
        }
        return await res.json();
    } catch (err) {
        console.error("API GET error:", err);
        return { error: String(err) };
    }
}

export async function getHealth() {
    return apiGet("/health");
}

export async function getVersion() {
    return apiGet("/version");
}

export async function getConfig() {
    return apiGet("/config");
}

export async function getStatus() {
    return apiGet("/status");
}

export default {
    getHealth,
    getVersion,
    getConfig,
    getStatus,
};
