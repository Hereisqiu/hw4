import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts, type Product } from '../api'
import { CATEGORIES, categoryOf } from '../categories'
import { openChat } from '../chatBus'
import ProductCard from '../components/ProductCard'
import Bulldog from '../components/Bulldog'

const COLLAGE_IDS = ['basic-hoodie-big-yale', '2025-yale-vs-harvard-t-shirt', 'district-vit-hoodie-vintage-bulldog', 'baseball-left-chest-crewneck']

export default function Home() {
  const [products, setProducts] = useState<Product[]>([])

  useEffect(() => {
    fetchProducts().then(setProducts).catch(() => {})
  }, [])

  const collage = useMemo(
    () => COLLAGE_IDS.map(id => products.find(p => p.product_id === id)).filter((p): p is Product => !!p),
    [products],
  )
  const featured = useMemo(() => products.filter(p => /hood|crewneck/i.test(p.garment_type)).slice(0, 4), [products])
  const categoryCover = (key: string) => products.find(p => categoryOf(p) === key)
  const minPrice = (key: string) => Math.min(...products.filter(p => categoryOf(p) === key).map(p => p.price))

  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Est. on Broadway · New Haven, CT</p>
          <h1 className="varsity">
            Wear your<br /><span className="outline">Bulldog</span><br />pride.
          </h1>
          <p>
            Officially licensed Yale apparel for students, alumni, families, and fans: cozy hoodies,
            classic crewnecks, and game-day tees made for every season on campus.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn">Shop the collection</Link>
            <button className="btn ghost" onClick={() => openChat()}>Ask Dan for help</button>
          </div>
        </div>
        <div className="hero-collage" aria-hidden="true">
          {collage.map((p, i) => (
            <Link key={p.product_id} to={`/products/${p.product_id}`} className={`polaroid p${i}`} tabIndex={-1}>
              <img src={p.image_url} alt="" />
              <span>{p.name.replace(/\s\d+$/, '')}</span>
            </Link>
          ))}
          <div className="pennant"><span>YALE</span></div>
        </div>
      </section>

      <section className="page">
        <div className="section-head">
          <h2 className="varsity">Shop by category</h2>
          <Link to="/products" className="link">View all →</Link>
        </div>
        <div className="cat-grid">
          {CATEGORIES.map(c => {
            const cover = categoryCover(c.key)
            return (
              <Link key={c.key} to={`/products?category=${c.key}`} className="cat-tile">
                {cover && <img src={cover.image_url} alt="" loading="lazy" />}
                <div>
                  <strong>{c.label}</strong>
                  {products.length > 0 && <span>from ${minPrice(c.key).toFixed(0)}</span>}
                </div>
              </Link>
            )
          })}
        </div>

        <div className="dan-banner">
          <Bulldog size={88} />
          <div>
            <h3 className="varsity">Meet Dan, your shopping assistant</h3>
            <p>Ask about sizes, colors, stock, or gift ideas. Dan checks our live inventory, so the answers are always real.</p>
          </div>
          <button className="btn" onClick={() => openChat('What would make a good gift under $40?')}>Find a gift</button>
        </div>

        <div className="section-head">
          <h2 className="varsity">Fan favorites</h2>
        </div>
        <div className="grid">
          {featured.map((p, i) => <ProductCard key={p.product_id} product={p} index={i} />)}
        </div>

        <div className="tiles">
          <div className="tile"><span className="tile-icon">☕</span><h3>Everyday comfort</h3><p>Soft fleece and relaxed fits for long library nights and chilly walks across Old Campus.</p></div>
          <div className="tile"><span className="tile-icon">🏈</span><h3>Game-day ready</h3><p>Rivalry tees and team gear for The Game, the rink, the boathouse, and beyond.</p></div>
          <div className="tile"><span className="tile-icon">🎁</span><h3>Gifts for every Eli</h3><p>Something for the proud parent, the returning alum, and the newest member of the Class.</p></div>
        </div>
      </section>
    </>
  )
}
