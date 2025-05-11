import {
  BookOpen,
  DiscordLogo,
  GithubLogo,
  Briefcase,
  Envelope,
  Globe,
  HouseLine,
  Info,
  LinkSimple,
} from "@phosphor-icons/react"; // Keep imports for ICON_COMPONENTS
import React from "react";
import SettingsButton from "../SettingsButton";
import { isMobile } from "react-device-detect";
import { Tooltip } from "react-tooltip";

export const MAX_ICONS = 3;
export const ICON_COMPONENTS = {
  BookOpen: BookOpen,
  DiscordLogo: DiscordLogo,
  GithubLogo: GithubLogo,
  Envelope: Envelope,
  LinkSimple: LinkSimple,
  HouseLine: HouseLine,
  Globe: Globe,
  Briefcase: Briefcase,
  Info: Info,
};

export default function Footer() {

  // Force a completely custom rendering regardless of data
  return (
    <div className="mb-2">
      <div className="flex flex-col space-y-4">
        {/* Custom styled buttons with !important flags */}
        <a
          href="https://docs.google.com/spreadsheets/d/1HlErvgiT8YcCLymjS5vd8HaXi-RTbgMdGoiCapRqlhE/edit?usp=sharing"
          target="_blank"
          rel="noreferrer"
          style={{
            textAlign: 'center !important',
            width: '100% !important',
            padding: '12px !important',
            backgroundColor: 'var(--theme-sidebar-footer-icon) !important',
            borderRadius: '6px !important',
            marginBottom: '8px !important',
            color: 'var(--theme-sidebar-footer-icon-fill) !important',
            fontWeight: '500 !important'
          }}
          aria-label="Memories"
        >
          Memories
        </a>
        
        <a
          href="https://docs.google.com/spreadsheets/d/1ke9ONjoC4M9ASqB8_WCMeTYcZ-un0ROHWqzJePAKDqM/edit?gid=0#gid=0"
          target="_blank"
          rel="noreferrer"
          style={{
            textAlign: 'center !important',
            width: '100% !important',
            padding: '12px !important',
            backgroundColor: 'var(--theme-sidebar-footer-icon) !important',
            borderRadius: '6px !important',
            marginBottom: '8px !important',
            color: 'var(--theme-sidebar-footer-icon-fill) !important',
            fontWeight: '500 !important'
          }}
          aria-label="Logs"
        >
          Logs
        </a>
        
        <a
          href="https://calendar.google.com/calendar/u/1?cid=NGQ0MjU5MGI3M2JkM2ViODJjY2I0ZDM0YTQxNWY5MmE1N2U1ZTFmM2I0MDgxNGIwOTRiNWU4MTI4MjU4ZWUyN0Bncm91cC5jYWxlbmRhci5nb29nbGUuY29t"
          target="_blank"
          rel="noreferrer"
          style={{
            textAlign: 'center !important',
            width: '100% !important',
            padding: '12px !important',
            backgroundColor: 'var(--theme-sidebar-footer-icon) !important',
            borderRadius: '6px !important',
            color: 'var(--theme-sidebar-footer-icon-fill) !important',
            fontWeight: '500 !important'
          }}
          aria-label="Calendar"
        >
          Calendar
        </a>
        
        {!isMobile && <div className="flex justify-center"><SettingsButton /></div>}
      </div>
    </div>
  );
}
