import { useLocation } from 'react-router-dom'
import { useChatResults } from '../chatResults'
import ProductCard from './ProductCard'

export const RESULTS_ID = 'assistant-results'

export default function AssistantResults() {
  const { results, setResults } = useChatResults()
  const { pathname } = useLocation()
  // Product detail pages keep the large image at the top; results reappear when the customer goes back.
  if (!results || results.products.length === 0 || pathname.startsWith('/products/')) return null

  return (
    <section className="assistant-results page" id={RESULTS_ID} aria-live="polite">
      <div className="page-head">
        <div>
          <p className="eyebrow">Assistant picks</p>
          <h2>{results.title}</h2>
          <p className="muted">{results.products.length} {results.products.length === 1 ? 'item' : 'items'} · click a card for full details</p>
        </div>
        <button className="btn ghost small" onClick={() => setResults(null)}>Clear</button>
      </div>
      <div className="grid">
        {results.products.map((p, i) => <ProductCard key={p.product_id} product={p} index={i} />)}
      </div>
    </section>
  )
}
