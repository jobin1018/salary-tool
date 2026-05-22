import client from './client'

export async function getEmployees(params) {
  const { data } = await client.get('/api/v1/employees', { params })
  return data
}

export async function getFilters() {
  const { data } = await client.get('/api/v1/employees/filters')
  return data
}

export async function createEmployee(payload) {
  const { data } = await client.post('/api/v1/employees', payload)
  return data
}

export async function updateEmployee(id, payload) {
  const { data } = await client.patch(`/api/v1/employees/${id}`, payload)
  return data
}

export async function deleteEmployee(id) {
  await client.delete(`/api/v1/employees/${id}`)
}
