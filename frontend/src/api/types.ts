export interface Token {
  access_token: string;
  token_type: string;
}

export interface UserRead {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface PlanRead {
  id: number;
  name: string;
  price_cents: number;
  currency: string;
  interval: string;
}

export interface SubscriptionRead {
  id: number;
  status: string;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  plan: PlanRead | null;
  created_at: string;
}
