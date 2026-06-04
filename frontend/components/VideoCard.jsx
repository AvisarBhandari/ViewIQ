export default function VideoCard({ label, data }) {
  const engRate = data.metadata.views
    ? (((data.metadata.likes + data.metadata.comments) / data.metadata.views) * 100).toFixed(2)
    : "—";

  return (
    <div className="p-4 border-b border-zinc-200 dark:border-zinc-800">
      <div className="text-xs font-medium text-zinc-400 uppercase tracking-wide mb-2">
        {label}
      </div>

      <div className="w-full aspect-video bg-zinc-100 dark:bg-zinc-800 rounded-lg flex items-center justify-center mb-3 border border-zinc-200 dark:border-zinc-700">
        <svg className="w-8 h-8 text-zinc-400" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8 5v14l11-7L8 5z"/>
        </svg>
      </div>

      <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100 line-clamp-2 mb-1">
        {data.metadata.title}
      </p>
      <p className="text-xs text-zinc-500 mb-3">
        {data.metadata.creator} · {data.metadata.duration}
      </p>

      <div className="grid grid-cols-3 gap-2">
        {[
          { label: "Views", value: fmtNum(data.metadata.views) },
          { label: "Likes", value: fmtNum(data.metadata.likes) },
          { label: "Eng. rate", value: `${engRate}%`, highlight: true },
        ].map((s) => (
          <div key={s.label} className="bg-zinc-50 dark:bg-zinc-800 rounded-md p-2">
            <div className="text-[10px] text-zinc-400">{s.label}</div>
            <div className={`text-sm font-medium ${s.highlight ? "text-green-600 dark:text-green-400" : "text-zinc-900 dark:text-zinc-100"}`}>
              {s.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function fmtNum(n) {
  if (!n) return "—";
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return String(n);
}