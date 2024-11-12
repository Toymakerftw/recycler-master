// API service for making requests to the backend
const API_BASE_URL = '/api';

export const api = {
    // Client management
    async getClients() {
        const response = await fetch(`${API_BASE_URL}/clients`);
        return response.json();
    },

    async addClient(clientIp) {
        const response = await fetch(`${API_BASE_URL}/clients`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ client_ip: clientIp }),
        });
        return response.json();
    },

    async removeClient(clientIp) {
        const response = await fetch(`${API_BASE_URL}/clients/${clientIp}`, {
            method: 'DELETE',
        });
        return response.json();
    },

    // File management
    async getClientFiles(clientIp) {
        const response = await fetch(`${API_BASE_URL}/clients/${clientIp}/files`);
        return response.json();
    },

    async downloadFile(clientIp, filePath) {
        window.open(`${API_BASE_URL}/clients/${clientIp}/files/${filePath}`);
    },
};
