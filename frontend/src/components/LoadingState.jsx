export function LoadingState({ message = "Loading..." }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4">
      <div className="w-10 h-10 border-4 border-[#e94560] border-t-transparent rounded-full animate-spin" />
      <p className="text-gray-400 text-sm">{message}</p>
    </div>
  );
}

export function EmptyState({ message = "Nothing found.", icon = "🎬" }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-3 text-center">
      <span className="text-5xl">{icon}</span>
      <p className="text-gray-400">{message}</p>
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
      <span className="text-5xl">⚠️</span>
      <p className="text-red-400 max-w-md">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-[#e94560] text-white rounded-lg hover:bg-red-600 transition-colors"
        >
          Try again
        </button>
      )}
    </div>
  );
}
