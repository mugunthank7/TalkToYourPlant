import { createRoot } from "react-dom/client";
import App from "./App";
import { BotGallery } from "./ui/Volty";
import "./styles.css";
import "./hud.css";
import { clock, startClock } from "./clock";

startClock();
{
  const q = new URLSearchParams(location.search);
  if (q.get("t")) clock.t = Number(q.get("t"));
  if (q.get("speed")) clock.speed = Number(q.get("speed"));
  if (q.get("pause")) clock.playing = false;
}
if (new URLSearchParams(location.search).get("clean")) document.body.classList.add("clean");

createRoot(document.getElementById("root")!).render(new URLSearchParams(location.search).get("botdemo") ? <BotGallery /> : <App />);
