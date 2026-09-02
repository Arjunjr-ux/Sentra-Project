import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import App from './App.jsx'

describe('App scaffold', () => {
  it('renders the Sentra wordmark', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    )
    expect(screen.getByRole('heading', { name: 'Sentra' })).toBeInTheDocument()
  })
})
