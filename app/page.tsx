import Link from "next/link";

export default function HomePage() {
  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-semibold text-ink-900 mb-3">
        Monitor Monetario Argentina
      </h1>
      <p className="text-ink-700 leading-relaxed mb-6">
        Base histórica y visualización de agregados monetarios del BCRA, con
        foco en su interacción con el financiamiento del Tesoro. Este es un
        proyecto en construcción por etapas; hoy está disponible la primera
        sección, con datos reales del BCRA.
      </p>
      <Link
        href="/agregados"
        className="inline-block rounded-md bg-accent text-white px-4 py-2 text-sm font-medium hover:bg-accent-muted transition-colors"
      >
        Ver agregados monetarios →
      </Link>
    </div>
  );
}
