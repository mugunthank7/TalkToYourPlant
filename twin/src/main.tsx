import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";
import { startClock } from "./clock";

startClock();

createRoot(document.getElementById("root")!).render(<App />);
