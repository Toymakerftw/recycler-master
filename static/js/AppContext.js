import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from './api';

const AppContext = createContext();

export function AppProvider({ children }) {
    const [clients, setClients] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchClients = async () => {
        try {
            setLoading(true);
            const data = await api.getClients();
            setClients(data.clients);
        } catch (err) {
            setError('Failed to fetch clients');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchClients();
    }, []);

    const addClient = async (clientIp) => {
        try {
            const result = await api.addClient(clientIp);
            if (result.success) {
                await fetchClients();
                return { success: true };
            }
            return { success: false, message: result.message };
        } catch (err) {
            console.error(err);
            return { success: false, message: 'Failed to add client' };
        }
    };

    const removeClient = async (clientIp) => {
        try {
            const result = await api.removeClient(clientIp);
            if (result.success) {
                await fetchClients();
                return { success: true };
            }
            return { success: false, message: result.message };
        } catch (err) {
            console.error(err);
            return { success: false, message: 'Failed to remove client' };
        }
    };

    return (
        <AppContext.Provider value={{
            clients,
            loading,
            error,
            addClient,
            removeClient,
            refreshClients: fetchClients,
        }}>
            {children}
        </AppContext.Provider>
    );
}

export function useApp() {
    return useContext(AppContext);
}
