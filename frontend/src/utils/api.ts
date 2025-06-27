import axios, { AxiosResponse, AxiosError } from 'axios';
import {
  Contact,
  Deal,
  Activity,
  DashboardStats,
  ContactCreateRequest,
  ContactUpdateRequest,
  DealCreateRequest,
  DealUpdateRequest,
  ActivityCreateRequest,
  ActivityUpdateRequest,
  ApiError,
} from '../types';

// Get the correct backend URL - default to localhost if not set
const BACKEND_URL = (import.meta as any).env?.VITE_BACKEND_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 second timeout
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    console.error('API Error:', error);
    
    if (error.response?.data) {
      // Backend returned an error response
      const apiError: ApiError = {
        detail: (error.response.data as any).detail || 'An error occurred',
        status_code: error.response.status,
      };
      throw apiError;
    }
    
    if (error.request) {
      // Network error
      throw new Error('Network error: Unable to connect to the server');
    }
    
    // Other error
    throw new Error(error.message || 'An unexpected error occurred');
  }
);

// Generic API service class
class ApiService {
  // Contact methods
  async getContacts(search?: string): Promise<Contact[]> {
    try {
      const params = search ? { search } : {};
      const response: AxiosResponse<Contact[]> = await api.get('/contacts', { params });
      
      // Ensure we always return an array
      if (!Array.isArray(response.data)) {
        console.warn('API returned non-array data for contacts:', response.data);
        return [];
      }
      
      return response.data;
    } catch (error) {
      console.error('Error fetching contacts:', error);
      return []; // Return empty array on error to prevent crashes
    }
  }

  async getContact(id: string): Promise<Contact> {
    const response: AxiosResponse<Contact> = await api.get(`/contacts/${id}`);
    return response.data;
  }

  async createContact(data: ContactCreateRequest): Promise<Contact> {
    const response: AxiosResponse<Contact> = await api.post('/contacts', data);
    return response.data;
  }

  async updateContact(id: string, data: ContactUpdateRequest): Promise<Contact> {
    const response: AxiosResponse<Contact> = await api.put(`/contacts/${id}`, data);
    return response.data;
  }

  async deleteContact(id: string): Promise<void> {
    await api.delete(`/contacts/${id}`);
  }

  // Deal methods
  async getDeals(): Promise<Deal[]> {
    try {
      const response: AxiosResponse<Deal[]> = await api.get('/deals');
      
      // Ensure we always return an array
      if (!Array.isArray(response.data)) {
        console.warn('API returned non-array data for deals:', response.data);
        return [];
      }
      
      return response.data;
    } catch (error) {
      console.error('Error fetching deals:', error);
      return []; // Return empty array on error to prevent crashes
    }
  }

  async getDeal(id: string): Promise<Deal> {
    const response: AxiosResponse<Deal> = await api.get(`/deals/${id}`);
    return response.data;
  }

  async createDeal(data: DealCreateRequest): Promise<Deal> {
    const response: AxiosResponse<Deal> = await api.post('/deals', data);
    return response.data;
  }

  async updateDeal(id: string, data: DealUpdateRequest): Promise<Deal> {
    const response: AxiosResponse<Deal> = await api.put(`/deals/${id}`, data);
    return response.data;
  }

  async deleteDeal(id: string): Promise<void> {
    await api.delete(`/deals/${id}`);
  }

  // Activity methods
  async getActivities(contactId?: string, dealId?: string): Promise<Activity[]> {
    try {
      const params: Record<string, string> = {};
      if (contactId) params.contact_id = contactId;
      if (dealId) params.deal_id = dealId;
      
      const response: AxiosResponse<Activity[]> = await api.get('/activities', { params });
      
      // Ensure we always return an array
      if (!Array.isArray(response.data)) {
        console.warn('API returned non-array data for activities:', response.data);
        return [];
      }
      
      return response.data;
    } catch (error) {
      console.error('Error fetching activities:', error);
      return []; // Return empty array on error to prevent crashes
    }
  }

  async getActivity(id: string): Promise<Activity> {
    const response: AxiosResponse<Activity> = await api.get(`/activities/${id}`);
    return response.data;
  }

  async createActivity(data: ActivityCreateRequest): Promise<Activity> {
    const response: AxiosResponse<Activity> = await api.post('/activities', data);
    return response.data;
  }

  async updateActivity(id: string, data: ActivityUpdateRequest): Promise<Activity> {
    const response: AxiosResponse<Activity> = await api.put(`/activities/${id}`, data);
    return response.data;
  }

  async deleteActivity(id: string): Promise<void> {
    await api.delete(`/activities/${id}`);
  }

  // Dashboard methods
  async getDashboardStats(): Promise<DashboardStats> {
    try {
      const response: AxiosResponse<DashboardStats> = await api.get('/dashboard/stats');
      
      // Ensure deals_by_stage is always an object
      if (!response.data.deals_by_stage || typeof response.data.deals_by_stage !== 'object') {
        response.data.deals_by_stage = {
          'Lead': 0,
          'Qualified': 0,
          'Proposal': 0,
          'Negotiation': 0,
          'Closed Won': 0,
          'Closed Lost': 0,
        };
      }
      
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      // Return default stats on error
      return {
        total_contacts: 0,
        total_deals: 0,
        total_revenue: 0,
        pipeline_value: 0,
        deals_by_stage: {
          'Lead': 0,
          'Qualified': 0,
          'Proposal': 0,
          'Negotiation': 0,
          'Closed Won': 0,
          'Closed Lost': 0,
        }
      };
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();

// Export legacy APIs for backward compatibility
export const contactsApi = {
  getAll: (search?: string) => apiService.getContacts(search),
  getById: (id: string) => apiService.getContact(id),
  create: (data: ContactCreateRequest) => apiService.createContact(data),
  update: (id: string, data: ContactUpdateRequest) => apiService.updateContact(id, data),
  delete: (id: string) => apiService.deleteContact(id),
};

export const dealsApi = {
  getAll: () => apiService.getDeals(),
  getById: (id: string) => apiService.getDeal(id),
  create: (data: DealCreateRequest) => apiService.createDeal(data),
  update: (id: string, data: DealUpdateRequest) => apiService.updateDeal(id, data),
  delete: (id: string) => apiService.deleteDeal(id),
};

export const activitiesApi = {
  getAll: (contactId?: string, dealId?: string) => apiService.getActivities(contactId, dealId),
  getById: (id: string) => apiService.getActivity(id),
  create: (data: ActivityCreateRequest) => apiService.createActivity(data),
  update: (id: string, data: ActivityUpdateRequest) => apiService.updateActivity(id, data),
  delete: (id: string) => apiService.deleteActivity(id),
};

export const dashboardApi = {
  getStats: () => apiService.getDashboardStats(),
};

export default api; 