import { createBrowserRouter } from "react-router";
import Home from "./pages/Home";
import Results from "./pages/Results";
import { resultsLoader, compatibilityAction } from "./pages/loaders";

// Error component for better error handling
function ErrorBoundary() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-red-600 mb-4">Oops! Something went wrong</h2>
        <p className="text-gray-600">Please try refreshing the page or contact support if the problem persists.</p>
      </div>
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Home />,
    action: compatibilityAction,
    errorElement: <ErrorBoundary />,
  },
  {
    path: "/results",
    element: <Results />,
    loader: resultsLoader,
    errorElement: <ErrorBoundary />,
  },
]);
