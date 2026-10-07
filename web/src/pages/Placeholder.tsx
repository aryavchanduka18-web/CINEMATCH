export default function Placeholder({ title }: { title: string }) {
  return (
    <section>
      <h1 className="mb-2 text-2xl font-semibold">{title}</h1>
      <p className="text-sm text-white/60">Coming in a later phase.</p>
    </section>
  );
}