import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import { apiClient } from "../api/client";
import { clearToken, getToken } from "../api/auth";
import type { SubscriptionRead } from "../api/types";

export default function Dashboard() {
  const navigate = useNavigate();
  const hasToken = Boolean(getToken());
  const [canceling, setCanceling] = useState(false);

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
