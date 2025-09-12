import React, { useState } from 'react';

function App() {
  const [count, setCount] = useState(0);

  return (
    <div className="p-6 text-center">
      <h1 className="text-2xl font-bold">🚀 Zero Apps React Frontend</h1>
      <button
        className="mt-4 px-4 py-2 rounded bg-blue-600 text-white"
        onClick={() => setCount(count + 1)}
      >
        Count: {count}
      </button>
    </div>
  );
}

export default App;
