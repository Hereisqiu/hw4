import { useEffect } from 'react'
import { NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import Home from './pages/Home'
import Products from './pages/Products'
import ProductDetail from './pages/ProductDetail'
import About from './pages/About'
import Login from './pages/Login'
import Register from './pages/Register'
import ChatWidget from './components/ChatWidget'
import AssistantResults from './components/AssistantResults'
import Ticker from './components/Ticker'
import { useAuth } from './auth'

export default function App() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return (
    <>
      <Ticker />
      <header className="nav">
        <NavLink to="/" className="brand">
          <span className="brand-mark">CC</span>
          <span className="brand-text">Campus <span>Customs</span></span>
        </NavLink>
        <nav>
          <NavLink to="/" end>Home</NavLink>
          <NavLink to="/products">Products</NavLink>
          <NavLink to="/about">About Us</NavLink>
          {user ? (
            <>
              <span className="nav-user">Hi, {user.first_name || user.name}</span>
              <button className="nav-cta" onClick={() => logout().then(() => navigate('/'))}>Log out</button>
            </>
          ) : (
            <>
              <NavLink to="/login">Log in</NavLink>
              <NavLink to="/register" className="nav-cta">Create account</NavLink>
            </>
          )}
        </nav>
      </header>
      <main>
        <AssistantResults />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:id" element={<ProductDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="*" element={<p className="page">Page not found.</p>} />
        </Routes>
      </main>
      <footer className="footer">
        <div className="footer-inner">
          <div>
            <p className="brand-text">Campus <span>Customs</span></p>
            <p className="muted">Officially licensed Yale apparel since day one on Broadway.</p>
          </div>
          <div>
            <strong>Shop</strong>
            <NavLink to="/products?category=hoodies">Hoodies</NavLink>
            <NavLink to="/products?category=crewnecks">Crewnecks</NavLink>
            <NavLink to="/products?category=tees">T-shirts</NavLink>
          </div>
          <div>
            <strong>Visit</strong>
            <span>57 Broadway</span>
            <span>New Haven, CT 06511</span>
          </div>
        </div>
        <p className="footer-fine">© Campus Customs · Boola Boola 🐾</p>
      </footer>
      <ChatWidget />
    </>
  )
}
