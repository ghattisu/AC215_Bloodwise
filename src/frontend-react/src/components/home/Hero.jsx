import Link from 'next/link';
import styles from './Hero.module.css';


export default function Hero() {
    return (
        <section
            className="relative h-screen flex items-center justify-center text-center bg-black"
            style={{
                backgroundImage: "linear-gradient(rgba(0, 0, 0, 0.2), rgba(0, 0, 0, 0.2)), url('/assets/hero_background.png')",
                backgroundSize: 'cover',
                backgroundPosition: 'center'
            }}
        >
            <div className="container mx-auto px-4">
                <h1 className="text-5xl md:text-7xl font-playfair text-white mb-6">
                    🩸 Bloodwise is here!
                </h1>
                <p className="text-xl md:text-2xl text-white">
                    Interpret blood test results with AI
                </p>
                <Link href="/chat" className={styles.chatButton}>
                    Start Chat
                </Link>
            </div>
        </section>
    )
}