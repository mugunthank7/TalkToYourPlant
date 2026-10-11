import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";
import { startClock } from "./clock";

startClock();
if (new URLSearchParams(location.search).get("clean")) document.body.classList.add("clean");

createRoot(document.getElementById("root")!).render(<App />);
