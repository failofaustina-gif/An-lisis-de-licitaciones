"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

/**
 * Alta manual de un trimestre de PBI. Sin autenticación (decisión
 * tomada explícitamente): pega directo a /api/pbi. Ese route handler es
 * el único lugar con permiso de escritura (usa la service_role key en el
 * servidor); acá solo se arma y valida el request.
 */
export function CargarPbiForm() {
  const router = useRouter();
  const [date, setDate] = useState("");
  const [value, setValue] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setErrorMsg("");

    // Acepta tanto "850000000" como "850.000.000" o "850000000,5".
    const numericValue = Number(value.replace(/\./g, "").replace(",", "."));
    if (!Number.isFinite(numericValue) || numericValue <= 0) {
      setStatus("error");
      setErrorMsg("El valor tiene que ser un número mayor a 0.");
      return;
    }

    try {
      const res = await fetch("/api/pbi", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ date, value: numericValue }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error ?? "Error desconocido.");
      }
      setDate("");
      setValue("");
      setStatus("idle");
      router.refresh();
    } catch (err) {
      setStatus("error");
      setErrorMsg(err instanceof Error ? err.message : "Error desconocido.");
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      className="flex flex-wrap items-end gap-3 rounded-lg border border-ink-100 bg-white p-4"
    >
      <label className="flex flex-col gap-1 text-sm">
        <span className="text-ink-500">Fecha (fin de trimestre)</span>
        <input
          type="date"
          required
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="rounded-md border border-ink-100 px-3 py-2 text-sm"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        <span className="text-ink-500">PBI nominal (ARS millones)</span>
        <input
          type="text"
          inputMode="decimal"
          required
          placeholder="ej: 850.000.000"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="rounded-md border border-ink-100 px-3 py-2 text-sm w-48"
        />
      </label>
      <button
        type="submit"
        disabled={status === "loading"}
        className="rounded-md bg-accent text-white px-4 py-2 text-sm font-medium hover:bg-accent-muted transition-colors disabled:opacity-50"
      >
        {status === "loading" ? "Guardando…" : "Guardar"}
      </button>
      {status === "error" ? (
        <p className="w-full text-xs text-danger">{errorMsg}</p>
      ) : null}
    </form>
  );
}
