import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchProducts, type Product } from '../api'
import { CATEGORIES, SIZES, categoryOf } from '../categories'
import ProductCard from '../components/ProductCard'

type Sort = 'name' | 'price-asc' | 'price-desc' | 'stock'

export default function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [error, setError] = useState('')
  const [params, setParams] = useSearchParams()
  const query = params.get('q') ?? ''
  const category = params.get('category') ?? 'all'
  const size = params.get('size') ?? ''
  const sort = (params.get('sort') as Sort) ?? 'name'

  // Filters live in the URL so they survive "back" from a product page and can be shared.
  const update = (key: string, value: string) => {
    const next = new URLSearchParams(params)
    if (value && value !== 'all') next.set(key, value)
    else next.delete(key)
    setParams(next, { replace: true })
  }

  useEffect(() => {
    fetchProducts().then(setProducts).catch(e => setError(String(e)))
  }, [])

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: products.length }
    products.forEach(p => { const k = categoryOf(p); c[k] = (c[k] ?? 0) + 1 })
    return c
  }, [products])

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase()
    const list = products.filter(p => {
      if (category !== 'all' && categoryOf(p) !== category) return false
      if (size && !p.inventory?.some(i => i.size === size && i.quantity > 0)) return false
      if (!q) return true
      return [p.name, p.garment_type, p.description, ...p.colors, ...p.search_tags].join(' ').toLowerCase().includes(q)
    })
    const by: Record<Sort, (a: Product, b: Product) => number> = {
      name: (a, b) => a.name.localeCompare(b.name),
      'price-asc': (a, b) => a.price - b.price || a.name.localeCompare(b.name),
      'price-desc': (a, b) => b.price - a.price || a.name.localeCompare(b.name),
      stock: (a, b) => (b.total_stock ?? 0) - (a.total_stock ?? 0),
    }
    return [...list].sort(by[sort] ?? by.name)
  }, [products, query, category, size, sort])

  const filtered = query || category !== 'all' || size

  return (
    <section className="page">
      <div className="page-head">
        <h1>Products</h1>
        <input className="search" placeholder="Search hoodies, hockey, navy…" value={query} onChange={e => update('q', e.target.value)} />
      </div>

      <div className="chips" role="tablist" aria-label="Category">
        {[{ key: 'all', label: 'All' }, ...CATEGORIES, { key: 'other', label: 'Other' }]
          .filter(c => c.key === 'all' || counts[c.key])
          .map(c => (
            <button key={c.key} role="tab" aria-selected={category === c.key}
              className={`chip ${category === c.key ? 'active' : ''}`} onClick={() => update('category', c.key)}>
              {c.label} <span>{counts[c.key] ?? 0}</span>
            </button>
          ))}
      </div>

      <div className="toolbar">
        <label>
          In stock in
          <select value={size} onChange={e => update('size', e.target.value)}>
            <option value="">Any size</option>
            {SIZES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        <label>
          Sort
          <select value={sort} onChange={e => update('sort', e.target.value === 'name' ? '' : e.target.value)}>
            <option value="name">Name A–Z</option>
            <option value="price-asc">Price: low to high</option>
            <option value="price-desc">Price: high to low</option>
            <option value="stock">Most in stock</option>
          </select>
        </label>
        <span className="muted">{shown.length} {shown.length === 1 ? 'item' : 'items'}</span>
        {filtered && <button className="link-btn" onClick={() => setParams({}, { replace: true })}>Reset filters</button>}
      </div>

      {error && <p className="error">Could not load products: {error}</p>}
      {!error && products.length > 0 && shown.length === 0 && (
        <p className="muted">No products match these filters. Try another size or category, or ask the assistant.</p>
      )}
      <div className="grid">
        {shown.map((p, i) => <ProductCard key={p.product_id} product={p} index={i} highlightSize={size || undefined} />)}
      </div>
    </section>
  )
}
