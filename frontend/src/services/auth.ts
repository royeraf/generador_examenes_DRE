import { apiClient } from './api';

export interface Docente {
    dni: string;
    nombres: string;
    is_active: boolean;
    is_superuser: boolean;
}

export interface Token {
    access_token: string;
    token_type: string;
}

export const authService = {
    async login(dni: string, password: string): Promise<Token> {
        const formData = new FormData();
        formData.append('username', dni);
        formData.append('password', password);
        
        const response = await apiClient.post<Token>('/auth/login', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            }
        });
        
        if (response.data.access_token) {
            localStorage.setItem('token', response.data.access_token);
        }
        return response.data;
    },

    async register(dni: string, password: string, nombres: string): Promise<Docente> {
        const response = await apiClient.post<Docente>('/auth/register', {
            dni,
            password,
            nombres
        });
        return response.data;
    },

    async getMe(): Promise<Docente> {
        const response = await apiClient.get<Docente>('/auth/me');
        return response.data;
    },

    logout() {
        localStorage.removeItem('token');
    },

    isAuthenticated(): boolean {
        return !!localStorage.getItem('token');
    }
};
