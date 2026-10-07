import { useQuery } from "@tanstack/react-query";
import { fetchHealth } from "../api/health";

export default function HealthStatus() {
  const { data, isPending, isError } = useQuery({ queryKey: ["health"], queryFn: fetchHealth });

  if (isPending) return <p className="text-sm text-white/60">Checking API...</p>;
  if (isError) return <p className="text-sm text-white/60">API: unreachable</p>;
  return (
    <p className="text-sm text-white/60">
      API: {data.status}, DB: {data.db}
    </p>
  );
}