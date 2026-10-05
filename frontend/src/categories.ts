import type { Product } from './api'

// Catalogue garment types are free text; group them into shopper-friendly categories.
export const CATEGORIES: { key: string; label: string; test: RegExp }[] = [
  { key: 'hoodies', label: 'Hoodies', test: /hood/i },
  { key: 'crewnecks', label: 'Crewnecks', test: /crewneck|crew neck|mockneck/i },
  { key: 'quarter-zips', label: 'Quarter-zips', test: /quarter-zip|1\/4 zip/i },
  { key: 'tees', label: 'T-shirts', test: /t-shirt|tee/i },
  { key: 'outerwear', label: 'Fleece & jackets', test: /fleece|jacket|full-zip/i },
]

export function categoryOf(p: Product): string {
  const text = `${p.garment_type} ${p.name}`
  return CATEGORIES.find(c => c.test.test(text))?.key ?? 'other'
}

export const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
export const LOW_STOCK = 5
