import { Link } from 'react-router-dom'
import { formatPrice, type Product } from '../api'
import { LOW_STOCK } from '../categories'

function stockBadge(product: Product, size?: string): { text: string; tone: string } | null {
  if (!product.inventory) return null
  if (size) {
    const q = product.inventory.find(i => i.size === size)?.quantity ?? 0
    if (q === 0) return { text: `Sold out in ${size}`, tone: 'out' }
    if (q <= LOW_STOCK) return { text: `Only ${q} left in ${size}`, tone: 'low' }
    return null
  }
  if (!product.total_stock) return { text: 'Sold out', tone: 'out' }
  const soldOut = product.inventory.filter(i => i.quantity === 0).length
  if (soldOut >= 3) return { text: 'Limited sizes', tone: 'low' }
  return null
}

export default function ProductCard({ product, highlightSize, index = 0 }: { product: Product; highlightSize?: string; index?: number }) {
  const badge = stockBadge(product, highlightSize)
  return (
    <Link to={`/products/${product.product_id}`} className="card" style={{ animationDelay: `${Math.min(index, 12) * 40}ms` }}>
      <div className="card-img">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        {badge && <span className={`badge ${badge.tone}`}>{badge.text}</span>}
        <span className="card-cta">View details →</span>
      </div>
      <div className="card-body">
        <h3>{product.name}</h3>
        <p className="price">{formatPrice(product.price)}</p>
        <p className="desc">{product.description}</p>
      </div>
    </Link>
  )
}
