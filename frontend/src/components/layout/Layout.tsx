// The app shell shared by EVERY page:
//
//   ┌───────────────────────────────┐
//   │ Header (brand, user, logout)  │
//   │ Navbar (links)                │
//   │ main → <Outlet/> = the page   │  ← only this part swaps on navigation
//   │ Footer                        │
//   └───────────────────────────────┘
//
// Layout stays mounted across navigations (react-router swaps only the
// <Outlet/>), so the header never flickers or loses state.
import { Outlet } from 'react-router-dom'

import type { UserPublic } from '../../api/auth'
import Footer from './Footer'
import Header from './Header'
import Navbar from './Navbar'

interface Props {
  user: UserPublic
  onLogout: () => void
}

export default function Layout({ user, onLogout }: Props) {
  return (
    <div className="app-shell">
      <Header user={user} onLogout={onLogout} />
      <Navbar />
      <main className="app-main">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}
