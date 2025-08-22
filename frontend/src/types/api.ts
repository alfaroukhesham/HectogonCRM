// Base types
export interface BaseEntity {
  id: string;
  created_at: string;
  updated_at: string;
}

// Multi-tenancy types
export enum OrganizationPlan {
  FREE = 'free',
  BASIC = 'basic',
  PREMIUM = 'premium',
  ENTERPRISE = 'enterprise'
}

export interface CustomBranding {
  primaryColor?: string;
  secondaryColor?: string;
  logoUrl?: string;
  faviconUrl?: string;
  customCSS?: string;
  fontFamily?: string;
  brandName?: string;
  headerBackgroundColor?: string;
  sidebarBackgroundColor?: string;
  buttonColor?: string;
  linkColor?: string;
  // Add other branding properties as needed
}

export interface OrganizationSettings {
  timezone: string;
  date_format: string;
  currency: string;
  language: string;
  allow_user_registration: boolean;
  require_email_verification: boolean;
  max_users?: number;
  custom_branding: CustomBranding;
}

export interface Organization extends BaseEntity {
  name: string;
  slug: string;
  description?: string;
  plan: OrganizationPlan;
  logo_url?: string;
  website?: string;
  industry?: string;
  size?: string;
  settings: OrganizationSettings;
  is_active: boolean;
  created_by: string;
}

export interface OrganizationCreateRequest {
  name: string;
  slug?: string;
  description?: string;
  plan?: OrganizationPlan;
  logo_url?: string;
  website?: string;
  industry?: string;
  size?: string;
  settings?: Partial<OrganizationSettings>;
}

export interface OrganizationUpdateRequest extends Partial<OrganizationCreateRequest> {}

export enum MembershipRole {
  VIEWER = 'viewer',
  EDITOR = 'editor',
  ADMIN = 'admin'
}

export enum MembershipStatus {
  PENDING = 'pending',
  ACTIVE = 'active',
  SUSPENDED = 'suspended'
}

export interface Membership extends BaseEntity {
  user_id: string;
  organization_id: string;
  role: MembershipRole;
  status: MembershipStatus;
  joined_at: string;
  last_accessed?: string;
}

export interface OrganizationMembership {
  id: string;
  user_id: string;
  organization_id: string;
  organization_name: string;
  organization_slug: string;
  organization_logo_url?: string;
  role: MembershipRole;
  status: MembershipStatus;
  joined_at: string;
  last_accessed?: string;
}

export enum InvitationStatus {
  PENDING = 'pending',
  ACCEPTED = 'accepted',
  DECLINED = 'declined',
  EXPIRED = 'expired'
}

export interface Invitation extends BaseEntity {
  organization_id: string;
  email: string;
  role: MembershipRole;
  status: InvitationStatus;
  invited_by: string;
  expires_at: string;
  accepted_at?: string;
}

export interface InvitationCreateRequest {
  organization_id: string;
  email: string;
  role: MembershipRole;
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
  organization_id: string;
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
  organization_id: string;
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
  organization_id: string;
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
  total_activities: number;
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