// Base types
export interface BaseEntity {
  id: string;
  created_at: string;
  updated_at: string;
}

// Contact types
export interface Contact extends BaseEntity {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  company?: string;
  position?: string;
  address?: string;
  notes?: string;
}

export interface ContactCreateRequest {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  company?: string;
  position?: string;
  address?: string;
  notes?: string;
}

export interface ContactUpdateRequest extends Partial<ContactCreateRequest> {}

// Deal types
export type DealStage = 'Lead' | 'Qualified' | 'Proposal' | 'Negotiation' | 'Closed Won' | 'Closed Lost';

export interface Deal extends BaseEntity {
  title: string;
  contact_id: string;
  value: number;
  stage: DealStage;
  probability: number;
  expected_close_date?: string;
  description?: string;
}

export interface DealCreateRequest {
  title: string;
  contact_id: string;
  value: number;
  stage: DealStage;
  probability: number;
  expected_close_date?: string;
  description?: string;
}

export interface DealUpdateRequest extends Partial<DealCreateRequest> {}

// Activity types
export type ActivityType = 'Call' | 'Email' | 'Meeting' | 'Note' | 'Task';
export type ActivityPriority = 'Low' | 'Medium' | 'High';

export interface Activity extends BaseEntity {
  contact_id: string;
  type: ActivityType;
  title: string;
  description?: string;
  due_date?: string;
  priority: ActivityPriority;
  completed?: boolean;
}

export interface ActivityCreateRequest {
  contact_id: string;
  type: ActivityType;
  title: string;
  description?: string;
  due_date?: string;
  priority: ActivityPriority;
  completed?: boolean;
}

export interface ActivityUpdateRequest extends Partial<ActivityCreateRequest> {}

// Dashboard types
export interface DashboardStats {
  total_contacts: number;
  total_deals: number;
  total_revenue: number;
  pipeline_value: number;
  deals_by_stage: Record<DealStage, number>;
}

// API response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

// Form data types
export interface ContactFormData {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  company: string;
  position: string;
  address: string;
  notes: string;
}

export interface DealFormData {
  title: string;
  contact_id: string;
  value: string;
  stage: DealStage;
  probability: number;
  expected_close_date: string;
  description: string;
}

export interface ActivityFormData {
  contact_id: string;
  type: ActivityType;
  title: string;
  description: string;
  due_date: string;
  priority: ActivityPriority;
} 