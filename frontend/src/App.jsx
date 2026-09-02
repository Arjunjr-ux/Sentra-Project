import { Routes, Route } from 'react-router-dom'

function Placeholder() {
  return (
    <main className="scaffold">
      <div className="logo-mark">S</div>
      <h1>Sentra</h1>
      <p>User &amp; access management console — scaffold ready. UI arrives in Phase 3.</p>
    </main>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="*" element={<Placeholder />} />
    </Routes>
  )
}
