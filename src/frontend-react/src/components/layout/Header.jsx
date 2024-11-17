'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Home, Info, Podcasts, Email, SmartToy, ChatBubbleOutline } from '@mui/icons-material';
import styles from './Header.module.css';

export default function Header() {
    const pathname = usePathname();
    const router = useRouter();
    const [isScrolled, setIsScrolled] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);


    useEffect(() => {
        if (window) {
            const handleScroll = () => {
                setIsScrolled(window.scrollY > 50)
            }

            window.addEventListener('scroll', handleScroll)
            return () => window.removeEventListener('scroll', handleScroll)
        }

    }, []);
    useEffect(() => {
        if (window) {
            if (pathname === '/' && window.location.hash) {
                const element = document.getElementById(window.location.hash.slice(1));
                if (element) {
                    setTimeout(() => {
                        element.scrollIntoView({ behavior: 'smooth' });
                    }, 100);
                }
            }
        }
    }, [pathname]);

    // Handlers
    function buildHref(item) {

        let href = item.path;
        if ((pathname === "/") && (item.sectionId != '')) {
            href = `#${item.sectionId}`;
        } else {
            if ((item.path === "/") && (item.sectionId != '')) {
                href = item.path + `#${item.sectionId}`;
            } else {
                href = item.path;
            }
        }

        return href;
    }

    return (
        <header
            className={`fixed w-full top-0 z-50 transition-all duration-300 ${isScrolled ? 'bg-black/90' : 'bg-transparent'
                }`}
        >
            <div className="container mx-auto px-4 h-20 flex items-center justify-between">
                <Link href="/" className="text-white hover:text-white/90 transition-colors">
                    <h1 className="text-2xl font-bold font-montserrat">🩸 Bloodwise</h1>
                </Link>
            </div>
        </header>
    )
}