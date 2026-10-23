// Generic "under construction" page. Reused for every navbar link that
// has no real page yet — replace usages one by one as you build features.
interface Props {
  title: string
}

export default function PlaceholderPage({ title }: Props) {
  return (
    <section>
      <h1>{title}</h1>
      <p className="muted">🚧 Strona w przygotowaniu.</p>
    </section>
  )
}
