import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Toaster } from "sonner";
import { ThemeProvider } from "@/lib/themes/ThemeContext";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: {
    default: "Archboard - AI Architecture Design",
    template: "%s | Archboard"
  },
  description: "Transform your architecture diagrams into editable code with AI. Supports Mermaid, React Flow, Excalidraw, and multi-provider AI integration.",
  keywords: [
    "AI architecture design",
    "diagram editor",
    "Mermaid",
    "React Flow",
    "Excalidraw",
    "architecture visualization",
    "code generation",
    "system design",
    "flowchart maker"
  ],
  authors: [{ name: "Archboard Team" }],
  creator: "Archboard",
  publisher: "Archboard",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  manifest: "/manifest.json",
  icons: {
    icon: [
      { url: "/icon.svg", type: "image/svg+xml" },
      { url: "/icons/favicon-16.png", sizes: "16x16", type: "image/png" },
      { url: "/icons/favicon-32.png", sizes: "32x32", type: "image/png" }
    ],
    apple: [
      { url: "/apple-icon.png", sizes: "180x180", type: "image/png" }
    ],
    other: [
      {
        rel: "mask-icon",
        url: "/icon.svg",
        color: "#4f46e5"
      }
    ]
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://archboard.dev",
    title: "Archboard - AI Architecture Design",
    description: "Transform your architecture diagrams into editable code with AI. Supports Mermaid, React Flow, and Excalidraw.",
    siteName: "Archboard",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Archboard - Architecture Design Platform"
      }
    ]
  },
  twitter: {
    card: "summary_large_image",
    title: "Archboard - AI Architecture Design",
    description: "Transform your architecture diagrams into editable code with AI",
    images: ["/twitter-card.png"],
    creator: "@archboard"
  },
  viewport: {
    width: "device-width",
    initialScale: 1,
    maximumScale: 5,
    userScalable: true,
  },
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0f172a" }
  ],
  category: "technology",
  applicationName: "Archboard",
  appleWebApp: {
    capable: true,
    title: "Archboard",
    statusBarStyle: "black-translucent",
  },
  formatDetection: {
    telephone: false,
    email: false,
    address: false,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider>
          {children}
          <Toaster position="bottom-right" richColors theme="light" />
        </ThemeProvider>
      </body>
    </html>
  );
}
