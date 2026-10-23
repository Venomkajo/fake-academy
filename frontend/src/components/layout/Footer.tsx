// Page footer — fully static, no props, no state.
// {new Date().getFullYear()} keeps the copyright year correct forever.
export default function Footer() {
  return (
    <footer className="app-footer">
      <div className="container">
        <span>Fake Academy © {new Date().getFullYear()}</span>
        <span>Projekt edukacyjny — React + FastAPI</span>
      </div>
    </footer>
  )
}
