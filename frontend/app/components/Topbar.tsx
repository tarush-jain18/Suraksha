"use client";

import { Menu, Search } from "lucide-react";

export default function Topbar() {
  return (
    <header className="topbar">
      <div className="mobile-menu">
        <Menu size={22} />
      </div>

      <div className="search-box">
        <Search size={18} />
        <span>Search cyclone, location or region...</span>
      </div>

      <div className="topbar-right">
        <div className="online">
          <span />
          System Online
        </div>

        <div className="top-divider" />

        <div className="date">☼ &nbsp; 30 Sep 2026</div>

        <div className="time">11:02 AM</div>

        <div className="avatar">TJ</div>
      </div>
    </header>
  );
}