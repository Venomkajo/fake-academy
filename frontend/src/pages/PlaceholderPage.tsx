// Generic "under construction" page. Reused for every navbar link that
// has no real page yet — replaced one by one with real pages as the app grows.
interface Props {
  title: string
}

export default function PlaceholderPage({ title }: Props) {
  return (
    <section>
      <h1>{title}</h1>
      <p className="muted">Strona w przygotowaniu.</p>
    </section>
  )
}
