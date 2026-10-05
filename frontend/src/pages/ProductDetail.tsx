import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice, type Product } from '../api'
import { openChat } from '../chatBus'
import Bulldog from '../components/Bulldog'

export default function ProductDetail() {
  const { id = '' } = useParams()
  const [product, setProduct] = useState<Product | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    setProduct(null)
    fetchProduct(id).then(setProduct).catch(e => setError(String(e)))
  }, [id])

  if (error) return <p className="page error">Product not found.</p>
  if (!product) return <p className="page muted">Loading…</p>

  return (
    <section className="page">
      <Link to="/products" className="back">← All products</Link>
      <div className="detail">
        <div className="detail-img">
          <img src={product.image_url} alt={product.name} />
        </div>
        <div className="detail-info">
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="price big">{formatPrice(product.price)}</p>
          <p>{product.description}</p>
          <p><strong>Colors:</strong> {product.colors.join(', ')}</p>
          {product.inventory && product.inventory.length > 0 && (
            <>
              <h3>Sizes &amp; stock</h3>
              <div className="sizes">
                {product.inventory.map(i => (
                  <div key={i.size} className={`size ${i.quantity === 0 ? 'out' : ''}`}>
                    <strong>{i.size}</strong>
                    <span>{i.quantity === 0 ? 'Sold out' : `${i.quantity} left`}</span>
                  </div>
                ))}
              </div>
            </>
          )}
          <button className="ask-dan" onClick={() => openChat()}>
            <Bulldog size={36} />
            <span><strong>Questions about this?</strong> Ask Dan about fit, colors or stock</span>
          </button>
          <div className="tags">{product.search_tags.map(t => <span key={t}>{t}</span>)}</div>
        </div>
      </div>
    </section>
  )
}
