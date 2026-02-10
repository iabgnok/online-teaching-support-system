import { render, screen, fireEvent } from '@testing-library/vue'
import Contacts from '../src/views/Contacts.vue'
import api from '../src/api'
import { vi } from 'vitest'

vi.mock('../src/api')

test('renders contacts tabs and list', async () => {
  api.get.mockImplementation((url) => {
    if (url === '/contacts') return Promise.resolve({ data: [{ id: 1, real_name: 'Bob', username: 'bob', display_name: 'Bobby', is_online: true }] })
    if (url === '/contacts/requests') return Promise.resolve({ data: { incoming: [], outgoing: [] } })
    return Promise.resolve({ data: [] })
  })

  render(Contacts)

  // Should show Contacts tab
  expect(await screen.findByText('联系人')).toBeTruthy()
  expect(await screen.findByText('Bobby')).toBeTruthy()
})
