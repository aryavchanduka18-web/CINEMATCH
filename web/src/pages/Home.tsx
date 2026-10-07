import HealthStatus from "../components/HealthStatus";

export default function Home() {
  return (
    <section>
      <h1 className="mb-2 text-2xl font-semibold">Home</h1>
      <HealthStatus />
    </section>
  );
}