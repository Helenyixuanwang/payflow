import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import { apiClient } from "../api/client";
import { clearToken, getToken } from "../api/auth";
import type { CheckoutSessionResponse, PlanRead, SubscriptionRead } from "../api/types";

function formatPrice(priceCents: number, currency: string): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: currency.toUpperCase() }).format(
    priceCents / 100
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const hasToken = Boolean(getToken());
  const [canceling, setCanceling] = useState(false);
  const [subscribingPlanId, setSubscribingPlanId] = useState<number | null>(null);
  const [subscribeError, setSubscribeError] = useState<string | null>(null);

  useEffect(() => {
    if (!hasToken) {
      navigate("/login");
    }
  }, [hasToken, navigate]);

  const { data: subscription, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["subscription"],
    queryFn: async () => {
      const { data } = await apiClient.get<SubscriptionRead | null>("/billing/subscription");
      return data;
    },
    enabled: hasToken,
  });

  const hasNoSubscription = !isLoading && !isError && !subscription;

  const { data: plans, isLoading: plansLoading, isError: plansError } = useQuery({
    queryKey: ["plans"],
    queryFn: async () => {
      const { data } = await apiClient.get<PlanRead[]>("/billing/plans");
      return data;
    },
    enabled: hasToken && hasNoSubscription,
  });

  useEffect(() => {
    if (isAxiosError(error) && error.response?.status === 401) {
      clearToken();
      navigate("/login");
    }
  }, [error, navigate]);

  function handleLogout() {
    clearToken();
    navigate("/login");
  }

  async function handleCancel() {
    const confirmed = window.confirm(
      "Cancel your subscription? You'll keep access until the current period ends."
    );
    if (!confirmed) {
      return;
    }
    setCanceling(true);
    try {
      await apiClient.post("/billing/subscription/cancel");
      await refetch();
    } finally {
      setCanceling(false);
    }
  }

  async function handleSubscribe(planId: number) {
    setSubscribeError(null);
    setSubscribingPlanId(planId);
    try {
      const { data } = await apiClient.post<CheckoutSessionResponse>("/billing/checkout-session", {
        plan_id: planId,
      });
      window.location.href = data.checkout_url;
    } catch {
      setSubscribeError("Couldn't start checkout. Please try again.");
      setSubscribingPlanId(null);
    }
  }

  if (!hasToken) {
    return null;
  }

  return (
    <div>
      <h1>Dashboard</h1>
      <button type="button" onClick={handleLogout}>
        Log out
      </button>

      <section>
        <h2>Subscription</h2>
        {isLoading && <p>Loading...</p>}
        {isError && <p role="alert">Couldn't load subscription status.</p>}
        {hasNoSubscription && (
          <div>
            <p>No active subscription.</p>
            {plansLoading && <p>Loading plans...</p>}
            {plansError && <p role="alert">Couldn't load plans.</p>}
            {plans && (
              <ul>
                {plans.map((plan) => (
                  <li key={plan.id}>
                    {plan.name} — {formatPrice(plan.price_cents, plan.currency)}/{plan.interval}{" "}
                    <button
                      type="button"
                      onClick={() => handleSubscribe(plan.id)}
                      disabled={subscribingPlanId === plan.id}
                    >
                      {subscribingPlanId === plan.id ? "Redirecting..." : "Subscribe"}
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {subscribeError && <p role="alert">{subscribeError}</p>}
          </div>
        )}
        {subscription && (
          <>
            <dl>
              <dt>Plan</dt>
              <dd>{subscription.plan?.name ?? "Unknown"}</dd>

              <dt>Status</dt>
              <dd>{subscription.status}</dd>

              {!subscription.cancel_at_period_end && (
                <>
                  <dt>Renews on</dt>
                  <dd>{new Date(subscription.current_period_end).toLocaleDateString()}</dd>
                </>
              )}
            </dl>

            {subscription.status === "active" && !subscription.cancel_at_period_end && (
              <button type="button" onClick={handleCancel} disabled={canceling}>
                {canceling ? "Canceling..." : "Cancel Subscription"}
              </button>
            )}

            {subscription.cancel_at_period_end && (
              <p>
                Your subscription will end on{" "}
                {new Date(subscription.current_period_end).toLocaleDateString()}.
              </p>
            )}
          </>
        )}
      </section>
    </div>
  );
}
