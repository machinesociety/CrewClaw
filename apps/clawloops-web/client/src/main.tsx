import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

function injectAnalyticsScript() {
  const endpoint = import.meta.env.VITE_ANALYTICS_ENDPOINT?.trim();
  const websiteId = import.meta.env.VITE_ANALYTICS_WEBSITE_ID?.trim();

  if (!endpoint || !websiteId) {
    return;
  }

  const normalizedEndpoint = endpoint.replace(/\/+$/, "");
  const scriptSrc = `${normalizedEndpoint}/umami`;

  if (document.querySelector(`script[src="${scriptSrc}"]`)) {
    return;
  }

  const script = document.createElement("script");
  script.defer = true;
  script.src = scriptSrc;
  script.dataset.websiteId = websiteId;
  document.head.appendChild(script);
}

injectAnalyticsScript();

createRoot(document.getElementById("root")!).render(<App />);
