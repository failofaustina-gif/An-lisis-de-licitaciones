import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Monitor Monetario Argentina",
  description:
    "Seguimiento de la política monetaria y la liquidez en Argentina: agregados monetarios del BCRA e interacción con las licitaciones del Tesoro.",
};

const NAV_ITEMS = [
  { href: "/agregados", label: "Agregados monetarios" },
  { href: "/cargar-pbi", label: "Cargar PBI" },
  // Las siguientes secciones se agregan en próximas etapas del proyecto:
  // { href: "/licitaciones", label: "Licitaciones del Tesoro" },
  // { href: "/liquidez", label: "Tesoro y liquidez" },
  // { href: "/metodologia", label: "Metodología" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es-AR">
      <body>
        <div className="min-h-screen flex flex-col">
          <header className="border-b border-ink-100">
            <div className="mx-auto max-w-6xl px-4 sm:px-6 py-4 flex flex-wrap items-baseline justify-between gap-3">
              <Link href="/" className="group">
                <span className="text-lg font-semibold tracking-tight text-ink-900">
                  Monitor Monetario Argentina
                </span>
                <span className="block text-xs text-ink-500">
                  Política monetaria y liquidez · BCRA y Tesoro
                </span>
              </Link>
              <nav className="flex gap-5 text-sm">
                {NAV_ITEMS.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="text-ink-700 hover:text-accent transition-colors"
                  >
                    {item.label}
                  </Link>
                ))}
              </nav>
            </div>
          </header>

          <main className="flex-1 mx-auto w-full max-w-6xl px-4 sm:px-6 py-8">
            {children}
          </main>

          <footer className="border-t border-ink-100 mt-12">
            <div className="mx-auto max-w-6xl px-4 sm:px-6 py-6 text-xs text-ink-500">
              Fuente: BCRA — API de Estadísticas Monetarias v4.0. Datos originales
              sin modificar; ver detalle de cada serie en su tarjeta.
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
