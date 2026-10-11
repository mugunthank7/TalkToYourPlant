import { useState } from "react";

export interface HelpText { title: string; what: string; read: string; why: string }

/** A small "?" that opens a popover with what the thing is, how to read it, and why it matters. */
export function Help({ title, what, read, why }: HelpText) {
  const [open, setOpen] = useState(false);
  return (
    <span className="help" onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)} onFocus={() => setOpen(true)} onBlur={() => setOpen(false)}>
      <button type="button" className="hbtn" aria-label={`About ${title}`} onClick={() => setOpen(!open)}>?</button>
      {open && (
        <div className="hpop" role="tooltip">
          <b>{title}</b>
          <p><em>What it is</em> {what}</p>
          <p><em>How to read it</em> {read}</p>
          <p><em>Why it matters</em> {why}</p>
        </div>
      )}
    </span>
  );
}
