// app/page.tsx
'use client';
import { useState } from 'react';


export default function Home() {
    const [url, setUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);


    const submit = async (e: any) => {
        e.preventDefault(); setLoading(true);
        try {
            const r = await fetch('http://127.0.0.1:8000/api/ingest/youtube', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });
            const d = await r.json(); setResult(d);
        } finally { setLoading(false); }
    };


    return (
        <main className="min-h-screen max-w-2xl mx-auto p-6 space-y-6">
            <h1 className="text-3xl font-semibold">NoteSpark</h1>
            <form onSubmit={submit} className="flex gap-2">
                <input className="flex-1 border rounded-xl px-4 py-3" placeholder="Paste YouTube URL" value={url} onChange={e => setUrl(e.target.value)} />
                <button className="px-5 py-3 rounded-xl bg-black text-white" disabled={loading || !url}> {loading ? 'Working…' : 'Summarize'} </button>
            </form>
            {result && (
                <section className="space-y-3">
                    <h2 className="text-xl font-medium">Summary</h2>
                    <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded-xl">{result.summary}</pre>
                    {result.timestamps && (
                        <details className="p-4 border rounded-xl">
                            <summary className="cursor-pointer">Timestamps</summary>
                            <ul className="list-disc pl-6">
                                {result.timestamps.map((t: any, i: number) => (
                                    <li key={i}>{t.time} — {t.text}</li>
                                ))}
                            </ul>
                        </details>
                    )}
                </section>
            )}
        </main>
    );
}