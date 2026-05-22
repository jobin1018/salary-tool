import client from './client'

export async function getSummary() {
  const { data } = await client.get('/api/v1/insights/summary')
  return data
}

export async function getCountryStats(country) {
  const { data } = await client.get(`/api/v1/insights/country/${encodeURIComponent(country)}`)
  return data
}

export async function getCountryJobTitles(country) {
  const { data } = await client.get(`/api/v1/insights/country/${encodeURIComponent(country)}/job-titles`)
  return data
}

export async function getJobTitleStats(country, jobTitle) {
  const { data } = await client.get(
    `/api/v1/insights/country/${encodeURIComponent(country)}/job-title/${encodeURIComponent(jobTitle)}`
  )
  return data
}
