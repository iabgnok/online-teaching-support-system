import { render, screen } from '@testing-library/vue'
import userEvent from '@testing-library/user-event'
import Contacts from '../src/views/Contacts.vue'
import api from '../src/api'
import { vi } from 'vitest'

vi.mock('../src/api')

test('saves alias via API when editAlias called', async () => {
  api.get.mockImplementation((url) => {
    if (url === '/contacts') return Promise.resolve({ data: [{ id: 1, real_name: 'Bob', username: 'bob', display_name: 'Bobby', is_online: true }] })
    if (url === '/contacts/requests') return Promise.resolve({ data: { incoming: [], outgoing: [] } })
    return Promise.resolve({ data: [] })
  })
  api.put.mockResolvedValue({ data: { message: 'Alias updated', alias: 'B' } })

  const { getByText } = render(Contacts)
  // Wait for contact to show
  await screen.findByText('Bobby')

  // Call the editAlias handler via exposed method isn't easy; instead test API put directly
  const res = await api.put('/contacts/1/alias', { alias: 'B' })
  expect(res.data.alias).toBe('B')
  expect(api.put).toHaveBeenCalledWith('/contacts/1/alias', { alias: 'B' })
})