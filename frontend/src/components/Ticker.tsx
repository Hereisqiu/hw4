const ITEMS = [
  'Officially licensed Yale apparel',
  'Visit us at 57 Broadway, New Haven',
  'Game-day tees for Harvard–Yale',
  'Ask Dan, our shopping assistant, about sizes & stock',
  'Hoodies, crewnecks, quarter-zips & more',
  'Boola Boola',
]

export default function Ticker() {
  const row = ITEMS.map(t => <span key={t}>{t}<b>✦</b></span>)
  return (
    <div className="ticker" aria-label="Store announcements">
      <div className="ticker-track">{row}{row}</div>
    </div>
  )
}
