import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import { apiClient } from "../api/client";
import { clearToken, getToken } from "../api/auth";
import type { SubscriptionRead } from "../api/types";

export default function Dashboard() {
  const navigate = useNavigate();
  const hasToken = Boolean(getToken());

  useEffect(() => {
    if (!hasToken) {
      navigate("/login");
    }
  }, [hasToken, navigate]);

  const { data: subscription, isLoading, isError, error } = useQuery({
    queryKey: ["subscription"],
    queryFn: async () => {
      const { data } = await apiClient.get<SubscriptionRead | null>("/billing/subscription");
      return data;
    },
    enabled: hasToken,
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
        {!isLoading && !isError && !subscription && <p>No active subscription.</p>}
        {subscription && (
          <dl>
            <dt>Plan</dt>
            <dd>{subscription.plan?.name ?? "Unknown"}</dd>

            <dt>Status</dt>
            <dd>{subscription.status}</dd>

            <dt>{subscription.cancel_at_period_end ? "Ends on" : "Renews on"}</dt>
            <dd>{new Date(subscription.current_period_end).toLocaleDateString()}</dd>
          </dl>
        )}
      </section>
    </div>
  );
}
