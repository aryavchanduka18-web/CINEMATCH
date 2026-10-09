import { AnimatePresence, motion } from "framer-motion";
import { Outlet } from "react-router-dom";
import Footer from "./Footer";
import MobileTabBar from "./MobileTabBar";
import NavBar from "./NavBar";
import { useUI } from "./ui";
import QuickViewPanel from "../card/QuickViewPanel";
import GuestBanner from "../account/GuestBanner";
import WhyPanel from "../explain/WhyPanel";
import DislikeReasonSheet from "../feedback/DislikeReasonSheet";

export default function AppShell() {
  const { toast } = useUI();
  return (
    <div className="min-h-screen bg-bg text-ink">
      <NavBar />
      <GuestBanner />
      <main>
        <Outlet />
      </main>
      <Footer />
      <MobileTabBar />
      <QuickViewPanel />
      <WhyPanel />
      <DislikeReasonSheet />
      <AnimatePresence>
        {toast && (
          <motion.div
            role="status"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            transition={{ duration: 0.18 }}
            className="fixed bottom-20 left-1/2 z-50 -translate-x-1/2 rounded-md bg-white px-4 py-2 text-sm font-medium text-black shadow-lg md:bottom-8"
          >
            {toast}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}