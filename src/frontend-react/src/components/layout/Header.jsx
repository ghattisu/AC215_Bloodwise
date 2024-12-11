"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Bloodtype } from "@mui/icons-material";

const navItems = [
  { name: "Home", path: "/", sectionId: "", icon: <Home fontSize="small" /> },
  {
    name: "Bloodwise Assistant",
    path: "/chat",
    sectionId: "",
    icon: <Bloodtype fontSize="small" />,
  },
];

export default function Header() {
  const pathname = usePathname();
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const buildHref = (item) => {
    if (pathname === "/" && item.sectionId) {
      return `#${item.sectionId}`;
    }
    return item.path + (item.sectionId ? `#${item.sectionId}` : "");
  };

  const handleMobileMenuClick = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  return (
    <header
      className={`fixed w-full top-0 z-50 transition-all duration-300 ${
        isScrolled ? "bg-white/90" : "bg-transparent"
      }`}
    >
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link
            href="/"
            className="text-black hover:text-black/90 transition-colors"
          >
            <h1 className="text-2xl font-bold font-montserrat">🩸 Bloodwise</h1>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            {navItems.map((item) => (
              <Link
                key={item.name}
                href={buildHref(item)}
                className={`flex items-center space-x-2 text-black opacity-80 hover:opacity-100 transition-opacity ${
                  pathname === item.path ? "opacity-100" : ""
                }`}
              >
                <span>{item.icon}</span>
                <span className="text-sm">{item.name}</span>
              </Link>
            ))}
          </nav>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2 text-white"
            onClick={handleMobileMenuClick}
            aria-label="Toggle menu"
          >
            <div className="w-6 space-y-1">
              <span
                className={`block w-6 h-0.5 bg-black transition-all duration-300 ${
                  isMobileMenuOpen ? "rotate-45 translate-y-1.5" : ""
                }`}
              />
              <span
                className={`block w-6 h-0.5 bg-black transition-all duration-300 ${
                  isMobileMenuOpen ? "opacity-0" : ""
                }`}
              />
              <span
                className={`block w-6 h-0.5 bg-black transition-all duration-300 ${
                  isMobileMenuOpen ? "-rotate-45 -translate-y-1.5" : ""
                }`}
              />
            </div>
          </button>
        </div>

        {/* Mobile Menu */}
        <div className={`md:hidden ${isMobileMenuOpen ? "block" : "hidden"}`}>
          <nav className="absolute left-0 right-0 bg-white/95 mt-2 py-4 px-4 space-y-2">
            {navItems.map((item) => (
              <Link
                key={item.name}
                href={buildHref(item)}
                className="flex items-center space-x-4 text-black py-3 opacity-80 hover:opacity-100 transition-opacity"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                <span>{item.icon}</span>
                <span>{item.name}</span>
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}
