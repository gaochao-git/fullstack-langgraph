import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { configureAuthInterceptor } from "./utils/authInterceptor";
import "./global.css";
import App from "./App.tsx";

// Configure auth interceptor
configureAuthInterceptor({
  onUnauthorized: () => {
    window.location.href = '/login';
  }
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>
);
